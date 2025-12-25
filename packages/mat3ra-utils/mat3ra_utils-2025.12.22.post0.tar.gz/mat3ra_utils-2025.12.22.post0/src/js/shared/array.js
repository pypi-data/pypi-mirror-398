import flatten from "lodash/flatten";
import isArray from "lodash/isArray";
import keys from "lodash/keys";
import uniq from "lodash/uniq";

export function safeMakeArray(x) {
    if (!isArray(x)) return [x];
    return x;
}

/**
 * @summary Returns objects array in compact csv format. E.g.:
 * [{a: 1, b: 2}, {a: 2, d: 3}] -> [['a','b','d'],[1, 2, null], [2, null, 3]]
 * @param objects
 */
export function convertToCompactCSVArrayOfObjects(objects) {
    const headers = uniq(flatten(objects.map((x) => keys(x))));
    const result = [headers];
    objects.forEach((x) => {
        const row = [];
        headers.forEach((header) => {
            // eslint-disable-next-line no-prototype-builtins
            row.push(x.hasOwnProperty(header) ? x[header] : null);
        });
        result.push(row);
    });

    return result;
}

/**
 * @summary Function to sort array based on the order given in a separate array
 * @param arr {Array<number|string|object>}: input array to sort
 * @param order {Array<number|string|object>}: define the order of item in array
 * @return {Array<number|string|object>}
 */
export function sortArrayByOrder(arr, order) {
    const orderMap = new Map();
    order.forEach((item, index) => orderMap.set(item, index));

    return arr.sort((a, b) => {
        const indexA = orderMap.has(a) ? orderMap.get(a) : order.length;
        const indexB = orderMap.has(b) ? orderMap.get(b) : order.length;
        return indexA - indexB;
    });
}

/**
 * Normalizes data to an array format.
 * @param data {any} - The input data which can be of any type.
 * @returns {any[]}
 */
export function normalizeToArray(data) {
    if (Array.isArray(data)) {
        return data.flat();
    }
    if (data && typeof data === "object" && !Array.isArray(data) && !data.name) {
        return Object.values(data).flat();
    }
    return [data];
}
