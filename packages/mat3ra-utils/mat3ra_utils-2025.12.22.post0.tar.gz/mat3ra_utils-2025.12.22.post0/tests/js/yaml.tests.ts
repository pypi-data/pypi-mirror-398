import { expect } from "chai";
import fs from "fs";
import path from "path";

import { readYAMLFileSync, writeYAMLFileSync } from "../../src/js/server/yaml";
import { convertJSONToYAMLString, convertYAMLStringToJSON } from "../../src/js/shared/yaml";

describe("YAML operations", () => {
    const testDir = path.join(__dirname, "fixtures");
    const testFilePath = path.join(testDir, "test.yml");

    before(() => {
        if (!fs.existsSync(testDir)) {
            fs.mkdirSync(testDir, { recursive: true });
        }
    });

    after(() => {
        // Cleanup test files
        if (fs.existsSync(testFilePath)) {
            fs.unlinkSync(testFilePath);
        }
        if (fs.existsSync(testDir)) {
            fs.rmdirSync(testDir);
        }
    });

    it("should write and read YAML files", () => {
        const testData = {
            name: "test",
            values: [1, 2, 3],
            nested: {
                key: "value",
            },
        };

        writeYAMLFileSync(testFilePath, testData);
        const readData = readYAMLFileSync(testFilePath);
        expect(readData).to.deep.equal(testData);
    });

    it("should handle empty objects", () => {
        const emptyData = {};
        writeYAMLFileSync(testFilePath, emptyData);
        const readData = readYAMLFileSync(testFilePath);
        expect(readData).to.deep.equal(emptyData);
    });

    it("should handle arrays", () => {
        const arrayData = [
            { id: 1, name: "first" },
            { id: 2, name: "second" },
            { id: 3, name: "third" },
        ];
        writeYAMLFileSync(testFilePath, arrayData);
        const readData = readYAMLFileSync(testFilePath);
        expect(readData).to.deep.equal(arrayData);
    });

    it("should write YAML with custom options", () => {
        const testData = {
            description: "This is a very long line that should normally be folded",
            key: "value",
        };
        writeYAMLFileSync(testFilePath, testData, { lineWidth: 20 });
        const readData = readYAMLFileSync(testFilePath);
        expect(readData).to.deep.equal(testData);
    });

    it("should handle complex nested structures", () => {
        const complexData = {
            level1: {
                level2: {
                    level3: {
                        array: [1, 2, 3],
                        string: "test",
                        boolean: true,
                        number: 42,
                    },
                },
            },
        };
        writeYAMLFileSync(testFilePath, complexData);
        const readData = readYAMLFileSync(testFilePath);
        expect(readData).to.deep.equal(complexData);
    });

    it("should throw error when reading non-existent file", () => {
        const nonExistentPath = path.join(testDir, "nonexistent.yml");
        expect(() => readYAMLFileSync(nonExistentPath)).to.throw();
    });
});

describe("YAML to JSON conversion", () => {
    const yamlString = `name: test
values:
  - 1
  - 2
  - 3
nested:
  key: value
`;
    const jsonObject = {
        name: "test",
        values: [1, 2, 3],
        nested: {
            key: "value",
        },
    };

    it("should convert YAML string to JSON", () => {
        expect(convertYAMLStringToJSON(yamlString)).to.deep.equal(jsonObject);
    });

    it("should convert JSON to YAML string", () => {
        expect(convertJSONToYAMLString(jsonObject)).to.equal(yamlString);
    });
});
