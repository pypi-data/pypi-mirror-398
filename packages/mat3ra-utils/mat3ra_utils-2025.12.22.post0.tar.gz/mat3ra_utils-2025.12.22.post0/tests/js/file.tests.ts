import { expect } from "chai";
import fs from "fs";
import path from "path";

import { cleanDirectorySync, createObjectPathFromFilePath } from "../../src/js/server/file";

describe("file utilities", () => {
    it("should create an object path from a file path", () => {
        const thisFile = "/code.js/tests/utils/file.tests.js";
        const objectPath = createObjectPathFromFilePath(thisFile, "/code.js");
        expect(objectPath).to.be.equal("['tests']['utils']['file.tests']");
    });
});

describe("cleanDirectorySync", () => {
    const testDir = path.join(__dirname, "fixtures", "clean-test");

    beforeEach(() => {
        if (fs.existsSync(testDir)) {
            fs.rmSync(testDir, { recursive: true, force: true });
        }
        fs.mkdirSync(testDir, { recursive: true });
    });

    afterEach(() => {
        if (fs.existsSync(testDir)) {
            fs.rmSync(testDir, { recursive: true, force: true });
        }
    });

    it("should remove all files and directories when no omitFiles specified", () => {
        fs.writeFileSync(path.join(testDir, "file1.txt"), "content1");
        fs.writeFileSync(path.join(testDir, "file2.txt"), "content2");
        fs.mkdirSync(path.join(testDir, "subdir"));
        fs.writeFileSync(path.join(testDir, "subdir", "nested.txt"), "nested");

        cleanDirectorySync(testDir);

        const files = fs.readdirSync(testDir);
        expect(files).to.be.empty;
    });

    it("should keep specified files and directories with omitFiles", () => {
        fs.writeFileSync(path.join(testDir, "keep.txt"), "keep");
        fs.writeFileSync(path.join(testDir, "remove.txt"), "remove");
        fs.mkdirSync(path.join(testDir, "keep-dir"));
        fs.mkdirSync(path.join(testDir, "remove-dir"));

        cleanDirectorySync(testDir, ["keep.txt", "keep-dir"]);

        const files = fs.readdirSync(testDir).sort();
        expect(files).to.deep.equal(["keep-dir", "keep.txt"]);
    });

    it("should handle non-existent directory gracefully", () => {
        const nonExistentDir = path.join(testDir, "does-not-exist");
        expect(() => cleanDirectorySync(nonExistentDir)).to.not.throw();
    });
});
