use walkdir::{WalkDir, DirEntry};
use regex::Regex;
use std::collections::{BTreeMap, BTreeSet};
use std::fs::File;
use std::io::{BufReader, BufRead, Read};
use std::path::{Path, PathBuf};
use git2::Repository;
use chrono::{DateTime, Utc};
use serde::Serialize;
use pyo3::prelude::*;
use serde_json::to_string;

// ------------------- STRUCTS -------------------

#[derive(Serialize, Debug)]
pub struct TodoItem {
    pub file_path: String,
    pub line_number: usize,
    pub line_content: String,
    pub git_commit_id: Option<String>,
    pub git_author: Option<String>,
    pub git_timestamp: Option<DateTime<Utc>>,
}

// Tree output (Python): group TodoItems by top-level directory ("root folder").
#[derive(Serialize, Debug)]
pub struct SectionNode {
    #[serde(rename = "type")]
    pub node_type: &'static str,
    pub name: String,
    pub children: Vec<TodoItem>,
}

pub struct ScanConfig<'a> {
    pub selected_dirs: &'a [&'a str],
    pub excluded_dirs: &'a [&'a str],
    pub excluded_extensions: &'a [&'a str],
    pub file_size_limit_mb: u64,
}

// ------------------- DEFAULTS -------------------

static DEFAULT_SELECTED_DIRS: &[&str] = &["."];
static DEFAULT_EXCLUDED_DIRS: &[&str] = &[".git"];
static DEFAULT_EXCLUDED_EXTENSIONS: &[&str] = &[
    "png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "mkv", "zip",
    "tar", "gz", "exe", "dll", "rlib", "pyc", "o", "class", "so",
    "jar", "bin", "ico", "ttf", "otf", ".keystore",
];

impl Default for ScanConfig<'static> {
    fn default() -> Self {
        Self {
            selected_dirs: DEFAULT_SELECTED_DIRS,
            excluded_dirs: DEFAULT_EXCLUDED_DIRS,
            excluded_extensions: DEFAULT_EXCLUDED_EXTENSIONS,
            file_size_limit_mb: 10,
        }
    }
}

// ------------------- GIT BLAME -------------------

fn git_blame_line(
    repo_path: &Path,
    file_path: &Path,
    line_number: usize,
) -> (Option<String>, Option<String>, Option<DateTime<Utc>>) {
    let repo = match Repository::open(repo_path) {
        Ok(r) => r,
        Err(_) => return (None, None, None),
    };

    let relative_path = match file_path.strip_prefix(repo_path) {
        Ok(p) => p,
        Err(_) => return (None, None, None),
    };

    let blame = match repo.blame_file(relative_path, None) {
        Ok(b) => b,
        Err(_) => return (None, None, None),
    };

    let hunk = match blame.get_line(line_number) {
        Some(h) => h,
        None => return (None, None, None),
    };

    let sig = hunk.final_signature();
    let time = sig.when();
    let datetime = DateTime::from_timestamp(time.seconds(), 0);

    (
        Some(hunk.final_commit_id().to_string()),
        sig.name().map(|s| s.to_string()),
        datetime,
    )
}

// ------------------- FILE/DIR FILTERS -------------------

fn should_enter_dir(entry: &DirEntry, excluded_dirs: &[&str]) -> bool {
    if entry.file_type().is_dir() {
        let name = entry.file_name().to_string_lossy();
        if excluded_dirs.iter().any(|d| *d == name) {
            return false;
        }
    }
    true
}

fn should_scan_file(
    path: &Path,
    excluded_extensions: &[&str],
    file_size_limit_mb: u64,
) -> bool {
    if !path.is_file() {
        return false;
    }

    if let Ok(meta) = path.metadata() {
        if meta.len() > file_size_limit_mb * 1024 * 1024 {
            return false;
        }
    }

    if let Some(ext) = path.extension().and_then(|s| s.to_str()) {
        let ext = ext.to_lowercase();
        if excluded_extensions.iter().any(|e| e.eq_ignore_ascii_case(&ext)) {
            return false;
        }
    }

    if let Ok(mut file) = File::open(path) {
        let mut buf = [0; 1024];
        if let Ok(n) = file.read(&mut buf) {
            if buf[..n].contains(&0) {
                return false;
            }
        }
    }

    true
}

// ------------------- SCAN FILE -------------------

fn scan_file(
    path: &Path,
    todo_re: &Regex,
    repo_path: &Path,
) -> std::io::Result<Vec<TodoItem>> {
    let reader = BufReader::new(File::open(path)?);
    let mut todos = Vec::new();

    for (i, line) in reader.lines().enumerate() {
        let line = line?;
        if let Some(caps) = todo_re.captures(&line) {
            let todo_text = caps
                .get(1)
                .map(|m| m.as_str().trim().to_string())
                .unwrap_or_default();
            let (commit, author, time) = git_blame_line(repo_path, path, i + 1);

            // Always return paths relative to the repo root so Rust and Python outputs match.
            // Example: `/app/INFO.md` -> `./INFO.md`.
            let file_path = match path.strip_prefix(repo_path) {
                Ok(rel) => format!("./{}", rel.display()),
                Err(_) => path.display().to_string(),
            };
            todos.push(TodoItem {
                file_path,
                line_number: i + 1,
                // Keep only what's after `TODO` 
                line_content: todo_text,
                git_commit_id: commit,
                git_author: author,
                git_timestamp: time,
            });
        }
    }

    Ok(todos)
}

// Check if a file is tracked (or at least not ignored/untracked) by Git.
fn is_git_tracked(repo_path: &Path, file_path: &Path) -> bool {
    let repo = match Repository::open(repo_path) {
        Ok(r) => r,
        Err(_) => return false,
    };

    let relative_path = match file_path.strip_prefix(repo_path) {
        Ok(p) => p,
        Err(_) => return false,
    };

    match repo.status_file(relative_path) {
        Ok(status) => {
            // Skip if ignored or new (untracked). Treat all other states as tracked.
            !status.is_ignored() && !status.is_wt_new()
        }
        Err(_) => false,
    }
}

// ------------------- SCAN DIRECTORIES -------------------

pub fn scan_directories(config: &ScanConfig<'_>, repo_path: &Path) -> Vec<TodoItem> {
    // Capture group 1 is the todo message after `TODO` follower by `:` or  ` :`
    let todo_re = Regex::new(r"TODO\s*:\s*(.*)$").unwrap();
    let mut results = Vec::new();

    for root in config.selected_dirs {
        for entry in WalkDir::new(root)
            .into_iter()
            .filter_entry(|e| should_enter_dir(e, config.excluded_dirs))
            .filter_map(Result::ok)
        {
            let path = entry.path();
            if should_scan_file(path, config.excluded_extensions, config.file_size_limit_mb) {
                // Respect .gitignore and skip untracked files so we only report TODOs that Git knows about.
                if !is_git_tracked(repo_path, path) {
                    continue;
                }
                if let Ok(todos) = scan_file(path, &todo_re, repo_path) {
                    results.extend(todos);
                }
            }
        }
    }

    results
}

// ------------------- TREE OUTPUT (GROUP BY ROOT FOLDER) -------------------

fn list_root_folders(repo_root: &Path, excluded_dirs: &[&str]) -> BTreeSet<String> {
    let mut roots = BTreeSet::new();

    let entries = match std::fs::read_dir(repo_root) {
        Ok(e) => e,
        Err(_) => return roots,
    };

    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }
        let Some(name) = path.file_name().and_then(|s| s.to_str()) else {
            continue;
        };
        if excluded_dirs.iter().any(|d| *d == name) {
            continue;
        }
        roots.insert(name.to_string());
    }

    roots
}

fn build_todo_tree(
    todos: Vec<TodoItem>,
    repo_root: &Path,
    excluded_dirs: &[&str],
) -> Vec<SectionNode> {
    let root_folders_set = list_root_folders(repo_root, excluded_dirs);

    // `./backend` -> todos, `./frontend` -> todos, `./` -> root-level file todos
    let mut by_root: BTreeMap<String, Vec<TodoItem>> = BTreeMap::new();

    for todo in todos {
        // Expect `./path/...` from scan_file; fall back gracefully.
        let rel = todo.file_path.strip_prefix("./").unwrap_or(&todo.file_path);
        let mut parts = rel.splitn(2, '/');
        let first = parts.next().unwrap_or("");
        let rest = parts.next();

        // Group by repo top-level directories (root folders); everything else goes under "./".
        let root_name = match rest {
            Some(_) if root_folders_set.contains(first) => format!("./{}", first),
            _ => "./".to_string(),
        };

        by_root.entry(root_name).or_insert_with(Vec::new).push(todo);
    }

    // Sort todos within each section
    for todos in by_root.values_mut() {
        todos.sort_by(|a, b| a.file_path.cmp(&b.file_path).then_with(|| a.line_number.cmp(&b.line_number)));
    }

    by_root
        .into_iter()
        .map(|(name, children)| SectionNode {
            node_type: "section",
            name,
            children,
        })
        .collect()
}

// ------------------- PYTHON EXPORT -------------------

#[pyfunction]
fn scan_py(
    selected_dirs: Option<Vec<String>>,
    excluded_dirs: Option<Vec<String>>,
    excluded_extensions: Option<Vec<String>>,
    file_size_limit_mb: Option<u64>,
) -> PyResult<String> {
    let default = ScanConfig::default();

    // Ensure we use the actual Git workdir root as `repo_path`, otherwise scanning from a
    // non-root CWD would fail to open the repo and everything would be skipped.
    let repo_root: PathBuf = Repository::discover(".")
        .ok()
        .and_then(|r| r.workdir().map(|p| p.to_path_buf()))
        .unwrap_or_else(|| PathBuf::from("."));

    let selected_tmp;
    let selected_paths_tmp;
    let excluded_tmp;
    let extensions_tmp;

    let make_abs_dir = |dir: &str| -> String {
        let p = Path::new(dir);
        if p.is_absolute() {
            dir.to_string()
        } else {
            repo_root.join(p).to_string_lossy().to_string()
        }
    };

    let config = ScanConfig {
        selected_dirs: match selected_dirs {
            Some(ref v) => {
                selected_paths_tmp = v.iter().map(|s| make_abs_dir(s)).collect::<Vec<_>>();
                selected_tmp = selected_paths_tmp.iter().map(String::as_str).collect::<Vec<_>>();
                &selected_tmp
            }
            None => {
                selected_paths_tmp = vec![repo_root.to_string_lossy().to_string()];
                selected_tmp = selected_paths_tmp.iter().map(String::as_str).collect::<Vec<_>>();
                &selected_tmp
            }
        },
        excluded_dirs: match excluded_dirs {
            Some(ref v) => {
                excluded_tmp = v.iter().map(String::as_str).collect::<Vec<_>>();
                &excluded_tmp
            }
            None => default.excluded_dirs,
        },
        excluded_extensions: match excluded_extensions {
            Some(ref v) => {
                extensions_tmp = v.iter().map(String::as_str).collect::<Vec<_>>();
                &extensions_tmp
            }
            None => default.excluded_extensions,
        },
        file_size_limit_mb: file_size_limit_mb.unwrap_or(default.file_size_limit_mb),
    };

    let todos = scan_directories(&config, repo_root.as_path());
    let tree = build_todo_tree(todos, repo_root.as_path(), config.excluded_dirs);
    Ok(to_string(&tree).unwrap())
}

#[pymodule]
fn basecollab(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(scan_py, m)?)?;
    Ok(())
}

// ------------------- TESTS -------------------

#[cfg(test)]
mod tests {
    use super::*;
    use serial_test::serial;
    use std::path::Path;

    // Helper function that takes any config
    fn run_scan_test(config: &ScanConfig<'_>) {
        let todos = scan_directories(config, Path::new("."));
        println!("Found {} TODOs", todos.len());
        // Pretty Debug output (indented, multi-line)
        println!("{:#?}", todos);
    }

    #[test]
    #[serial]
    fn test_scan_default_config() {
        println!("Running default config test....................");
        let mut config = ScanConfig::default();
        config.file_size_limit_mb = 5;
        run_scan_test(&config);
    }

    // #[test]
    // #[serial]
    // fn test_scan_custom_config() {
    //     println!("Running custom config test.....................");
    //     // Configure directories, excluded dirs, extensions, file size, etc.
    //     let selected_dirs = ["."];
    //     let excluded_dirs = [".git", ".venv", "build"];
    //     let excluded_extensions = ["rs", "toml"];

    //     let config = ScanConfig {
    //         selected_dirs: &selected_dirs,
    //         excluded_dirs: &excluded_dirs,
    //         excluded_extensions: &excluded_extensions,
    //         file_size_limit_mb: 5,
    //     };

    //     run_scan_test(&config);
    // }
}
