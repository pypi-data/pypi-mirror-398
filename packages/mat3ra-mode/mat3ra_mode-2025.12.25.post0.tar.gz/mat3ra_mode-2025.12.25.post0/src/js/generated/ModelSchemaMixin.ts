import type { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import type { BaseModel } from "@mat3ra/esse/dist/js/types";

export type ModelSchemaMixin = BaseModel;

export type ModelInMemoryEntity = InMemoryEntity & ModelSchemaMixin;

export function modelSchemaMixin(item: InMemoryEntity) {
    // @ts-expect-error
    const properties: InMemoryEntity & ModelSchemaMixin = {
        get type() {
            return this.requiredProp<BaseModel["type"]>("type");
        },
        get subtype() {
            return this.requiredProp<BaseModel["subtype"]>("subtype");
        },
        get method() {
            return this.requiredProp<BaseModel["method"]>("method");
        },
    };

    Object.defineProperties(item, Object.getOwnPropertyDescriptors(properties));
}
