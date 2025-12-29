
up:
	docker compose up -d
down:
	docker compose down
restart:
	docker compose up -d --force-recreate
build:
	docker compose up -d --build --force-recreate
build_wheel:
	# Rebuild the Python wheel inside the running compose container (no image rebuild) then force reinstalls it.
	# Output persisted on host via volume: ./target/wheels/
	# Build for the current container platform (no manylinux enforcement). Use the Dockerfile build stage for a manylinux wheel.
	docker compose exec -T basecollab bash -lc "cd /app && git config --global --add safe.directory /app || true && rm -f target/wheels/*.whl && python -m pip install --no-cache-dir -q patchelf && maturin build --release --interpreter python3 && pip install --force-reinstall target/wheels/*.whl"
publish_wheel_dry:
	# Publish to TestPyPI (rehearsal). Requires TEST_PYPI_TOKEN in the container environment.
	docker compose exec -T basecollab bash -lc 'test -n "$$TEST_PYPI_TOKEN" || { echo "TEST_PYPI_TOKEN is missing"; exit 1; }; MATURIN_USERNAME=__token__ MATURIN_PASSWORD="$$TEST_PYPI_TOKEN" maturin publish --repository-url https://test.pypi.org/legacy/ --non-interactive --skip-existing'
publish_wheel:
	docker compose exec -T basecollab bash -lc 'test -n "$$PYPI_TOKEN" || { echo "PYPI_TOKEN is missing"; exit 1; }; MATURIN_USERNAME=__token__ MATURIN_PASSWORD="$$PYPI_TOKEN" maturin publish --repository-url https://upload.pypi.org/legacy/ --non-interactive --skip-existing'
rust_test : 
	cargo test -- --nocapture
python_test:
	# MAKE SURE build_wheel IS USED, SO IT MATCHES CURRENT RUST SOURCE !
	docker compose exec -T basecollab bash -lc "cd /app && python test.py"
