import { ApplicationSchemaBase, SlugifiedEntry } from "@mat3ra/esse/dist/js/types";
import MODELS_TREE_CONFIG_BY_APPLICATION from "@mat3ra/standata/dist/js/runtime_data/models/modelsTreeConfigByApplication.json";
import MODEL_TREE_DATA from "@mat3ra/standata/dist/js/runtime_data/models/modelTree.json";
import lodash from "lodash";

import type { ModelTree } from "./types";

export const { MODEL_TREE, MODEL_NAMES } = MODEL_TREE_DATA;

export const METHODS = {
    pseudopotential: "pseudopotential",
    localorbital: "localorbital",
    unknown: "unknown",
} as const;

export const getPseudopotentialTypesFromTree = (): string[] => {
    const dftTree = MODEL_TREE.dft as Record<string, any>;
    const firstBranch = Object.values(dftTree)[0];
    return firstBranch?.methods?.pseudopotential || [];
};

export const getDFTFunctionalsFromTree = (): string[] => {
    return Object.keys(MODEL_TREE.dft);
};

export const getDFTFunctionalsByApproximation = (approximation: string): string[] | undefined => {
    const dftTree = MODEL_TREE.dft as Record<string, any>;
    const branch = dftTree[approximation];
    return branch?.functionals;
};

export const treeSlugToNamedObject = (modelSlug: string): SlugifiedEntry => {
    return {
        slug: modelSlug,
        name: lodash.get(MODEL_NAMES, modelSlug, modelSlug),
    };
};

export const getTreeByApplicationNameAndVersion = ({
    name,
}: Pick<ApplicationSchemaBase, "name" | "version">): ModelTree => {
    // TODO: add logic to filter by version when necessary
    // @ts-ignore
    return MODELS_TREE_CONFIG_BY_APPLICATION[name] || {};
};

export const getDefaultModelTypeForApplication = (application: ApplicationSchemaBase): string => {
    return Object.keys(getTreeByApplicationNameAndVersion(application))[0];
};

export const getDefaultModelSubtypeForApplicationAndType = (
    application: ApplicationSchemaBase,
    type: string,
): string | undefined => {
    const tree = getTreeByApplicationNameAndVersion(application);
    const subtypes = Object.keys(tree[type] || {});
    return subtypes[0];
};
