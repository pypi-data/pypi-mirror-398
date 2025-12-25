import omit from "lodash/omit";

export function assertShallowDeepAlmostEqual(
    expect: object | boolean | number | null | string | Date,
    actual: object | boolean | number | null | string | Date,
    path = "",
    threshold = 0.01,
) {
    // null value
    if (expect === null) {
        if (!(actual === null)) {
            throw new Error(`Expected to have null but got "${actual}" at path "${path}".`);
        }

        return true;
    }

    // undefined expected value
    if (typeof expect === "undefined") {
        if (typeof actual !== "undefined") {
            throw new Error(`Expected to have undefined but got "${actual}" at path "${path}".`);
        }

        return true;
    }

    // scalar description
    if (typeof expect === "boolean" || typeof expect === "string") {
        if (expect !== actual) {
            throw new Error(`Expected to have "${expect}" but got "${actual}" at path "${path}".`);
        }

        return true;
    }

    // numbers — here is some important 'almost equal' stuff
    // TODO: configurable threshold
    if (typeof expect === "number") {
        if (typeof actual !== "number") {
            throw new Error(`Expected to have number but got "${actual}" at path "${path}".`);
        }
        if (Math.abs(expect - actual) > threshold) {
            throw new Error(
                `Expected to have "${expect}+-${threshold}" but got "${actual}" at path "${path}".`,
            );
        }

        return true;
    }

    // dates
    if (expect instanceof Date) {
        if (actual instanceof Date) {
            if (expect.getTime() !== actual.getTime()) {
                throw new Error(
                    `Expected to have date "${expect.toISOString()}" but got "${actual.toISOString()}" at path "${path}".`,
                );
            }
        } else {
            throw new Error(
                `Expected to have date "${expect.toISOString()}" but got "${actual}" at path "${path}".`,
            );
        }

        return true;
    }

    if (actual === null) {
        throw new Error(`Expected to have an array/object but got null at path "${path}".`);
    }

    // array/object description
    // eslint-disable-next-line no-restricted-syntax, guard-for-in
    for (const prop in expect) {
        // @ts-ignore
        if (typeof actual[prop] === "undefined" && typeof expect[prop] !== "undefined") {
            throw new Error(`Expected "${prop}" field to be defined at path "${path}".`);
        }

        const newPath = path + (path === "/" ? "" : "/") + prop;

        // @ts-ignore
        assertShallowDeepAlmostEqual(expect[prop], actual[prop], newPath, threshold);
    }

    return true;
}

export function assertDeepAlmostEqual(
    leftHandOperand: object,
    rightHandOperand: object,
    excludedKeys: string[] = [],
) {
    const expected = omit({ ...leftHandOperand }, excludedKeys);
    const actual = omit({ ...rightHandOperand }, excludedKeys);
    return assertShallowDeepAlmostEqual(expected, actual);
}
