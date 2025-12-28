import { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import { deepClone } from "@mat3ra/code/dist/js/utils";
import type { Constructor } from "@mat3ra/code/dist/js/utils/types";
import type { BaseMethod, SlugifiedEntry } from "@mat3ra/esse/dist/js/types";
import lodash from "lodash";

import { PseudopotentialMethodConfig } from "./default_methods";
import { type MethodSchemaMixin, methodSchemaMixin } from "./generated/MethodSchemaMixin";

type Base = typeof InMemoryEntity & Constructor<MethodSchemaMixin>;

interface MethodData extends Record<string, unknown> {
    searchText?: string;
}

export class Method extends (InMemoryEntity as Base) implements BaseMethod {
    constructor(config: BaseMethod) {
        const data = config.data || {};
        super({ ...config, data });
    }

    cloneWithoutData(): Method {
        const clone = this.clone() as Method;
        clone.setData({});
        return clone;
    }

    setSubtype(subtype: SlugifiedEntry): void {
        this.setProp("subtype", subtype);
    }

    static get defaultConfig(): BaseMethod {
        return PseudopotentialMethodConfig;
    }

    get searchText(): string {
        return this.prop<string>("data.searchText", "");
    }

    setSearchText(searchText: string): void {
        this.setData({ ...this.data, searchText });
    }

    setData(data: MethodData = {}): void {
        this.setProp("data", data);
    }

    get omitInHashCalculation(): boolean {
        const data = this.data as MethodData;
        return !data?.searchText && lodash.isEmpty(lodash.omit(data, "searchText"));
    }

    cleanData(fieldsToExclude: string[] = []): MethodData {
        const filteredData = { ...(this.data as MethodData) };
        fieldsToExclude.forEach((field) => {
            delete filteredData[field];
        });
        return filteredData;
    }

    toJSONWithCleanData(fieldsToExclude: string[] = []): BaseMethod {
        const json = { ...this._json, data: this.cleanData(fieldsToExclude) };
        return deepClone(json);
    }
}

methodSchemaMixin(Method.prototype);
