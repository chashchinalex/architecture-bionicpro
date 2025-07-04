.PHONY: up
up:
	open http://localhost:3000/
	docker compose up --remove-orphans --build
	