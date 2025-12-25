export function removeTimestampableKeysFromConfig(config: object) {
    // @ts-ignore
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { createdAt, updatedAt, removedAt, ...restConfig } = config;
    return restConfig;
}
