import { v4 as uuidv4, v5 as uuidv5 } from "uuid";

export function getUUID() {
    return uuidv4();
}

export function getUUIDFromNamespace(
    seed = "",
    namespace = "00000000-0000-4000-8000-000000000000",
) {
    return uuidv5(seed, namespace);
}
