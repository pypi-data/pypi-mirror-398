/* eslint-disable max-classes-per-file, class-methods-use-this */
import { expect } from "chai";

import { extendClass, extendThis } from "../../src/js/shared/class";

class BaseEntity {
    constructor(config: object) {
        Object.assign(this, config);
    }

    baseMethod() {
        return "base";
    }
}

class ExtendClassEntity extends BaseEntity {
    declare results: unknown;

    constructor(config: object, excluded = []) {
        super(config);
        extendClass(ExtendClassEntity, BaseEntity, excluded, [config]);
    }

    baseMethod() {
        return "derived";
    }
}

class BaseBetweenEntity {
    static staticAttr = "base";

    instanceAttr = "base";

    constructor(config: object) {
        Object.assign(this, config);
        this.instanceAttr = "base";
    }

    betweenMethod() {
        return "base";
    }
}

class BetweenEntity extends BaseBetweenEntity {
    static staticAttr = "between";

    constructor(config: object) {
        super(config);
        this.instanceAttr = "between";
    }

    betweenMethod() {
        return "between";
    }
}

class ExtendThisEntity extends BetweenEntity {
    declare results: unknown;

    constructor(config: object) {
        super(config);
        extendThis(ExtendThisEntity, BaseEntity, config);
    }

    baseMethod() {
        return "derived";
    }
}

describe("extendClass", () => {
    it("extends classes no excluded props", () => {
        const obj = new ExtendClassEntity({});
        expect(obj.baseMethod()).to.be.equal("base");
    });

    it("should support excluded props but doesnt", () => {
        const obj = new ExtendClassEntity({});
        expect(obj.baseMethod()).not.to.be.equal("derived");
    });

    it("should have results but doesnt", () => {
        const obj = new ExtendClassEntity({ results: ["test"] });
        expect(JSON.stringify(obj.results)).not.to.be.equal(JSON.stringify([{ name: "test" }]));
    });
});

describe("extendThis", () => {
    it("extends this prefer child method", () => {
        const obj = new ExtendThisEntity({});
        expect(obj.baseMethod()).to.be.equal("derived");
    });

    it("remembers intermediate methods", () => {
        const base = new BaseBetweenEntity({});
        expect(base.betweenMethod()).to.be.equal("base");
        const obj = new ExtendThisEntity({});
        expect(obj.betweenMethod()).to.be.equal("between");
    });

    it("propagates instance attributes", () => {
        const base = new BaseBetweenEntity({});
        expect(base.instanceAttr).to.be.equal("base");
        const obj = new ExtendThisEntity({});
        expect(obj.instanceAttr).to.be.equal("between");
    });

    it("propagates static attributes", () => {
        expect(BaseBetweenEntity.staticAttr).to.be.equal("base");
        expect(ExtendThisEntity.staticAttr).to.be.equal("between");
    });
});
