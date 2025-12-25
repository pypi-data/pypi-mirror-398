import { expect } from "chai";

import { deepClone } from "../../src/js/shared/clone";

interface TestObject {
    number: number;
    string: string;
    array: number[];
    object?: { a: string };
}

describe("deepClone", () => {
    const obj: TestObject = {
        number: 1.0,
        string: "test",
        array: [1.0],
        object: { a: "b" },
    };
    it("clones an object", () => {
        const clone = deepClone(obj);
        expect(clone).to.deep.equal(obj);
        expect(clone);
    });
    it("deep clones", () => {
        const clone = deepClone(obj);
        expect(clone).to.haveOwnProperty("object");
        delete obj.object;
        const other = deepClone(obj);
        expect(other).not.to.haveOwnProperty("object");
    });
});
