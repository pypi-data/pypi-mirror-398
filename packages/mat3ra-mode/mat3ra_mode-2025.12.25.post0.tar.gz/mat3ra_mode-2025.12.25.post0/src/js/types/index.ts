import type {
    ApplicationSchemaBase,
    BaseModel,
    CategorizedMethod,
    CategorizedModel,
    CategorizedUnitMethod,
} from "@mat3ra/esse/dist/js/types";

export type ModelConfig = Pick<BaseModel, "type" | "subtype"> &
    Partial<Omit<BaseModel, "type" | "subtype">> & {
        application?: ApplicationSchemaBase;
    };

export type SimplifiedCategorizedModel = Pick<
    CategorizedModel,
    "name" | "path" | "categories" | "parameters"
>;

export type SimplifiedCategorizedMethod = Pick<CategorizedMethod, "name" | "path"> & {
    units: CategorizedUnitMethod[];
};

export interface PseudopotentialLike {
    element?: string;
    toJSON(): Record<string, unknown>;
}

export type PseudopotentialCtor = new (config: Record<string, unknown>) => PseudopotentialLike;

export interface MethodTreeBranch {
    methods: Record<string, string[]>;
    functionals?: string[];
    refiners?: string[];
    modifiers?: string[];
}

export type ModelTree = Record<string, Record<string, MethodTreeBranch>>;
