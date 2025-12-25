import { expect } from "chai";

import {
    createSafeFilename,
    findPreviousVersion,
    renderTemplateString,
    renderTemplateStringWithEval,
} from "../../src/js/shared/str";

describe("findPreviousVersion", () => {
    const versions = ["5.4.2", "3.2", "6.2", "4", "7.2.1"];

    it("should find a previous semantic version", () => {
        const previous = findPreviousVersion(versions, "5.2");
        expect(previous).to.be.equal("4");
    });

    it("should return undefined if no previous version is found", () => {
        const previous = findPreviousVersion(versions, "2");
        // eslint-disable-next-line no-unused-expressions
        expect(previous).to.be.undefined;
    });
});

/* eslint-disable no-template-curly-in-string */
describe("Test string template expansion", () => {
    it("should expand test feature template with variables", () => {
        const template = "As a ${role}, I want to ${action}.";
        const context = {
            role: "User",
            action: "generate test cases automatically",
        };
        const expected = "As a User, I want to generate test cases automatically.";
        expect(renderTemplateString(template, context)).to.equal(expected);
    });

    it("should handle missing test feature variables", () => {
        const template = "Given ${precondition}, when ${action}, then ${result}";
        const context = {
            precondition: "the system is configured",
            action: "I run the test generator",
        };
        const expected =
            "Given the system is configured, when I run the test generator, then ${result}";
        expect(renderTemplateString(template, context)).to.equal(expected);
    });

    it("should handle empty test context", () => {
        const template = "Test Scenario: ${scenario_name}";
        const context = {};
        expect(renderTemplateString(template, context)).to.equal("Test Scenario: ${scenario_name}");
    });

    it("should handle test template without variables", () => {
        const template = "No variables";
        const context = { scenario_name: "No variables" };
        expect(renderTemplateString(template, context)).to.equal("No variables");
    });
});

/* eslint-disable no-template-curly-in-string */
describe("Test string template expansion with eval", () => {
    it("should expand test feature template with variables", () => {
        // @ts-ignore
        const padWithDashes = (x) => "---" + x + "---";
        const template = "As a ${role}, I want to ${action}. ${padWithDashes('test')}";
        const context = {
            role: "User",
            action: "generate test cases automatically",
            padWithDashes,
        };
        const expected = "As a User, I want to generate test cases automatically. ---test---";
        expect(renderTemplateStringWithEval(template, context)).to.equal(expected);
    });
});

describe("createSafeFilename", () => {
    it("should convert to lowercase, replace special chars with underscores, and trim", () => {
        expect(createSafeFilename("My File Name!")).to.equal("my_file_name");
        expect(createSafeFilename("Test@#$%/File123")).to.equal("test_file123");
        expect(createSafeFilename("---spaces and dashes---")).to.equal("spaces_and_dashes");
    });
});
