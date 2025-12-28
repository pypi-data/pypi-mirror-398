import { BaseMethod, BaseModel, SlugifiedEntry } from "@mat3ra/esse/dist/js/types";
import lodash from "lodash";

import { MODEL_NAMES, MODEL_TREE } from "./tree";

export const PseudopotentialMethodConfig: BaseMethod = {
    type: "pseudopotential",
    subtype: "us",
};

export const LocalOrbitalMethodConfig: BaseMethod = {
    type: "localorbital",
    subtype: "pople",
};

export const UnknownMethodConfig: BaseMethod = {
    type: "unknown",
    subtype: "unknown",
};

const mapSlugToNamedObject = (slug: string): SlugifiedEntry => {
    return {
        slug,
        name: lodash.get(MODEL_NAMES, slug, slug),
    };
};

export function allowedTypes(model: Pick<BaseModel, "type" | "subtype">): SlugifiedEntry[] {
    const branch = lodash.get(MODEL_TREE, `${model.type}.${model.subtype}.methods`, {});
    return lodash.keys(branch).map(mapSlugToNamedObject);
}

export function allowedSubtypes(model: Pick<BaseModel, "type" | "subtype">, type: string): SlugifiedEntry[] {
    const branch = lodash.get(MODEL_TREE, `${model.type}.${model.subtype}.methods.${type}`, []);
    return (branch as string[]).map(mapSlugToNamedObject);
}
