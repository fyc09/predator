.PHONY: release install test build compile

release: test build compile
	rm -rf build
	mkdir build
	cp dist build -r
	cp backend/dist build/server -r
	cp backend/runtime-package.json build/package.json
	echo "node ./server" >build/run.sh
	echo "node .\server" >build/run.bat
	cd build && npm install

install:
	npm install
	cd backend && npm install

test: install
	npm run test

build: install
	npm run build

compile: install
	cd backend && npm run compile

clean:
	rm -rf build dist node_modules
	rm -rf backend/coverage backend/dist backend/node_modules
