# .PHONY: setup-test teardown-test clean test-integration commit

clean:
	docker compose -f docker-compose.test.yml down -v


commit:
	uv run cz commit
