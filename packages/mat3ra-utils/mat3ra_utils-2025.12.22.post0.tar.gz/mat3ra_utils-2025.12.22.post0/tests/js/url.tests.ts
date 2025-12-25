import { expect } from "chai";

import { containsEncodedComponents } from "../../src/js/shared/url";

describe("containsEncodedComponents", () => {
    const decodedComponent = "a test with // special = characters?";
    const encodedComponent = encodeURIComponent(decodedComponent);

    it("identifies whether a string is URL encoded", () => {
        expect(containsEncodedComponents(encodedComponent)).to.be.true;
        expect(containsEncodedComponents(decodedComponent)).to.be.false;
    });
});
