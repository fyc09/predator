.PHONY: release install test cov build compile lint

release: cov build compile
	rm -rf build
	mkdir build
	cp dist build -r
	cp backend/dist build/server -r
	cp backend/runtime-package.json build/package.json
	printf "npm install && node ./server" >build/run.sh
	printf "npm install && node .\server" >build/run.bat

install:
	npm install
	cd backend && npm install

test: install
	npm run test

cov: install
	cd backend && npm run cov

build: install
	npm run build

compile: install
	cd backend && npm run compile

lint: install
	npm run lint

clean:
	rm -rf build dist node_modules
	rm -rf backend/coverage backend/dist backend/node_modules
