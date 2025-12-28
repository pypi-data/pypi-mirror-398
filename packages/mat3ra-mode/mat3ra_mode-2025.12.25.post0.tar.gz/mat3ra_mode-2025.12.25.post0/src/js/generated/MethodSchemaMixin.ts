import type { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import type { BaseMethod } from "@mat3ra/esse/dist/js/types";

export type MethodSchemaMixin = BaseMethod;

export type MethodInMemoryEntity = InMemoryEntity & MethodSchemaMixin;

export function methodSchemaMixin(item: InMemoryEntity) {
    // @ts-expect-error
    const properties: InMemoryEntity & MethodSchemaMixin = {
        get type() {
            return this.requiredProp<BaseMethod["type"]>("type");
        },
        get subtype() {
            return this.requiredProp<BaseMethod["subtype"]>("subtype");
        },
        get precision() {
            return this.prop<BaseMethod["precision"]>("precision");
        },
        get data() {
            return this.prop<BaseMethod["data"]>("data");
        },
    };

    Object.defineProperties(item, Object.getOwnPropertyDescriptors(properties));
}
