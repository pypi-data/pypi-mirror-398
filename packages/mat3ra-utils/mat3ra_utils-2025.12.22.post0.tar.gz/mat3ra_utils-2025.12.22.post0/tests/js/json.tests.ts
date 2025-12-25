import { expect } from "chai";
import fs from "fs";
import path from "path";

import { isJSONMinified, readJSONFileSync, writeJSONFileSync } from "../../src/js/server/json";

describe("JSON file operations", () => {
    const testDir = path.join(__dirname, "fixtures");
    const testFilePath = path.join(testDir, "test.json");

    before(() => {
        if (!fs.existsSync(testDir)) {
            fs.mkdirSync(testDir, { recursive: true });
        }
    });

    after(() => {
        if (fs.existsSync(testFilePath)) {
            fs.unlinkSync(testFilePath);
        }
        if (fs.existsSync(testDir)) {
            fs.rmdirSync(testDir);
        }
    });

    it("should write and read JSON files", () => {
        const testData = {
            name: "test",
            values: [1, 2, 3],
            nested: {
                key: "value",
            },
        };

        writeJSONFileSync(testFilePath, testData);
        const readData = readJSONFileSync(testFilePath);
        expect(readData).to.deep.equal(testData);
    });

    it("should write JSON with formatting", () => {
        const testData = { a: 1, b: 2 };
        writeJSONFileSync(testFilePath, testData, { spaces: 2 });
        const content = fs.readFileSync(testFilePath, "utf-8");
        expect(content).to.equal('{\n  "a": 1,\n  "b": 2\n}\n');
    });

    it("should write JSON without newline", () => {
        const testData = { a: 1 };
        writeJSONFileSync(testFilePath, testData, { addNewLine: false });
        const content = fs.readFileSync(testFilePath, "utf-8");
        expect(content).to.equal('{"a":1}');
    });

    it("should handle empty objects", () => {
        const emptyData = {};
        writeJSONFileSync(testFilePath, emptyData);
        const readData = readJSONFileSync(testFilePath);
        expect(readData).to.deep.equal(emptyData);
    });

    it("should handle arrays", () => {
        const arrayData = [1, 2, 3, { a: "b" }];
        writeJSONFileSync(testFilePath, arrayData);
        const readData = readJSONFileSync(testFilePath);
        expect(readData).to.deep.equal(arrayData);
    });

    it("should create directory if not exists", () => {
        const nestedPath = path.join(testDir, "nested", "deep", "test.json");
        const testData = { test: "data" };
        writeJSONFileSync(nestedPath, testData);
        expect(fs.existsSync(nestedPath)).to.be.true;
        const readData = readJSONFileSync(nestedPath);
        expect(readData).to.deep.equal(testData);
        fs.unlinkSync(nestedPath);
        fs.rmdirSync(path.dirname(nestedPath));
        fs.rmdirSync(path.dirname(path.dirname(nestedPath)));
    });

    it("should throw error when reading non-existent file", () => {
        const nonExistentPath = path.join(testDir, "nonexistent.json");
        expect(() => readJSONFileSync(nonExistentPath)).to.throw();
    });
});

describe("isJSONMinified", () => {
    const testDir = path.join(__dirname, "fixtures");
    const testFilePath = path.join(testDir, "test.json");

    before(() => {
        if (!fs.existsSync(testDir)) {
            fs.mkdirSync(testDir, { recursive: true });
        }
    });

    after(() => {
        if (fs.existsSync(testFilePath)) {
            fs.unlinkSync(testFilePath);
        }
    });

    it("should return true for minified JSON", () => {
        writeJSONFileSync(testFilePath, { a: 1, b: 2 }, { spaces: 0, addNewLine: false });
        expect(isJSONMinified(testFilePath)).to.be.true;
    });

    it("should return false for formatted JSON", () => {
        writeJSONFileSync(testFilePath, { a: 1 }, { spaces: 2 });
        expect(isJSONMinified(testFilePath)).to.be.false;
    });

    it("should return false for invalid JSON", () => {
        fs.writeFileSync(testFilePath, "{ invalid }", "utf-8");
        expect(isJSONMinified(testFilePath)).to.be.false;
    });
});
