import { safeMakeArray } from "@mat3ra/code/dist/js/utils";
import { BaseMethod } from "@mat3ra/esse/dist/js/types";
import _ from "underscore";

import { Method } from "../method";
import type { PseudopotentialCtor, PseudopotentialLike } from "../types";

export class PseudopotentialMethod extends Method {
    PseudopotentialCls: PseudopotentialCtor | null;

    constructor(config: BaseMethod) {
        super(config);
        this.PseudopotentialCls = null;
    }

    get pseudo(): Record<string, unknown>[] {
        return this.prop<Record<string, unknown>[]>("data.pseudo", []);
    }

    get allPseudo(): Record<string, unknown>[] {
        return this.prop<Record<string, unknown>[]>("data.allPseudo", []);
    }

    get pseudopotentials(): PseudopotentialLike[] {
        if (!this.PseudopotentialCls) return [];
        return this.pseudo.map((config) => new this.PseudopotentialCls!(config));
    }

    get allPseudopotentials(): PseudopotentialLike[] {
        if (!this.PseudopotentialCls) return [];
        return this.allPseudo.map((config) => new this.PseudopotentialCls!(config));
    }

    static extractExchangeCorrelationFromSubworkflow(subworkflow: any): {
        approximation: string;
        functional: string;
    } {
        const { model } = subworkflow;
        const approximation = model.subtype;
        const functionalValue = model.functional;
        const functional = functionalValue && (functionalValue.slug || functionalValue);
        return {
            approximation,
            functional: functional || "",
        };
    }

    hasPseudopotentialFor(element: string): boolean {
        return Boolean(this.pseudopotentials.find((pseudo) => pseudo.element === element));
    }

    setPseudopotentialPerElement(pseudo: PseudopotentialLike | undefined): void {
        if (!pseudo) {
            this.setPseudopotentials([]);
            return;
        }
        const filtered = this.pseudopotentials.filter((item) => item.element !== pseudo.element);
        filtered.push(pseudo);
        this.setPseudopotentials(filtered);
    }

    addToAllPseudos(pseudos: PseudopotentialLike | PseudopotentialLike[]): void {
        const list = safeMakeArray(pseudos);
        const all = this.allPseudopotentials;
        all.push(...list);
        this.setAllPseudopotentials(all);
    }

    setPseudopotentials(pseudopotentials: PseudopotentialLike[]): void {
        this.setData({
            ...this.data,
            pseudo: _.sortBy(pseudopotentials, "element").map((item) => item.toJSON()),
        });
    }

    setAllPseudopotentials(pseudopotentials: PseudopotentialLike[]): void {
        this.setData({
            ...this.data,
            allPseudo: _.sortBy(pseudopotentials, "element").map((item) => item.toJSON()),
        });
    }

    toJSONWithCleanData(exclude: string[] = []): BaseMethod {
        return super.toJSONWithCleanData(exclude.concat(["allPseudo"]));
    }
}
