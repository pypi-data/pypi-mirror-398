import { expect } from "chai";

import { assertDeepAlmostEqual, assertShallowDeepAlmostEqual } from "../../src/js/shared/assertion";

const OBJECT1 = { a: 1, b: { c: 2 } };
const OBJECT1_WITH_EXTRA_KEY = { a: 1, b: { c: 2 }, d: 3 };
const OBJECT1_EQUAL = { a: 1, b: { c: 2 } };
const OBJECT_EQUAL_WITHIN_TOLERANCE = { a: 1, b: { c: 2.009 } };
const OBJECT2 = { a: 1, b: { c: 3 } };

describe("assertShallowDeepAlmostEqual", () => {
    // Deep equality
    it("should assert two objects are deeply equal", () => {
        assertShallowDeepAlmostEqual(OBJECT1, OBJECT1_EQUAL);
    });

    it("should assert two objects are not equal", () => {
        expect(() => assertShallowDeepAlmostEqual(OBJECT1, OBJECT2)).to.throw(
            'Expected to have "2+-0.01" but got "3" at path "/b/c',
        );
    });
    it("should assert two objects are equal with almost equal numbers", () => {
        assertShallowDeepAlmostEqual(OBJECT1, OBJECT_EQUAL_WITHIN_TOLERANCE);
    });
    it("should assert two objects are not equal with almost equal numbers", () => {
        expect(() =>
            assertShallowDeepAlmostEqual(OBJECT1, OBJECT_EQUAL_WITHIN_TOLERANCE, "", 0.001),
        ).to.throw('Expected to have "2+-0.001" but got "2.009" at path "/b/c');
    });

    // Shallow equality
    it("should assert null values are equal", () => {
        assertShallowDeepAlmostEqual(null, null);
    });
    it("should assert null values are not equal", () => {
        expect(() => assertShallowDeepAlmostEqual(null, 1)).to.throw(
            'Expected to have null but got "1" at path ""',
        );
    });
});

describe("assertDeepAlmostEqual", () => {
    it("should assert two objects are deeply equal with excluded keys", () => {
        assertDeepAlmostEqual(OBJECT1, OBJECT1_WITH_EXTRA_KEY, ["d"]);
    });
    it("should assert two objects are not equal with excluded keys", () => {
        expect(() => assertDeepAlmostEqual(OBJECT1_WITH_EXTRA_KEY, OBJECT1)).to.throw(
            'Expected "d" field to be defined at path ""',
        );
    });
});
