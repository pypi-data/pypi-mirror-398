import { CategorizedModel, SlugifiedEntryOrSlug } from "@mat3ra/esse/dist/js/types";

import * as tree from "./tree";
import type { ModelConfig, SimplifiedCategorizedModel } from "./types";

export function safelyGetSlug(slugObj: SlugifiedEntryOrSlug): string {
    return typeof slugObj === "string" ? slugObj : slugObj.slug;
}

export class ModelConversionHandler {
    static convertToSimple(categorizedModel: CategorizedModel | undefined): ModelConfig {
        if (!categorizedModel) return this.convertUnknownToSimple();
        switch (categorizedModel.categories.tier3) {
            case "dft":
                return this.convertDftToSimple(categorizedModel);
            case "ml":
                return this.convertMlToSimple();
            default:
                return this.convertUnknownToSimple();
        }
    }

    static convertDftToSimple(categorizedModel: CategorizedModel): ModelConfig {
        if (!categorizedModel.categories?.subtype) return this.convertUnknownToSimple();
        const subtypeCategory = categorizedModel.categories.subtype as SlugifiedEntryOrSlug;
        const subtype = safelyGetSlug(subtypeCategory);
        const functionalParam = (categorizedModel.parameters as any)?.functional;
        const functionalSlug = functionalParam
            ? safelyGetSlug(functionalParam as SlugifiedEntryOrSlug)
            : "";
        return {
            type: "dft",
            subtype,
            functional: tree.treeSlugToNamedObject(functionalSlug),
        };
    }

    static convertMlToSimple(): ModelConfig {
        return {
            type: "ml",
            subtype: "re",
        };
    }

    static convertUnknownToSimple(): ModelConfig {
        return {
            type: "unknown",
            subtype: "unknown",
        };
    }

    static convertToCategorized(
        simpleModel: ModelConfig | undefined,
        allModels: CategorizedModel[] = [],
    ): SimplifiedCategorizedModel | undefined {
        switch (simpleModel?.type) {
            case "dft":
                return this.convertDftToCategorized(simpleModel, allModels);
            case "ml":
                return this.convertMlToCategorized(simpleModel);
            case "unknown":
                return undefined;
            default:
                return undefined;
        }
    }

    static convertDftToCategorized(
        simpleModel: ModelConfig,
        allModels: CategorizedModel[] = [],
    ): SimplifiedCategorizedModel | undefined {
        const { subtype, functional: functionalStringOrObject } = simpleModel;
        const defaultFunctionals: Record<string, string> = {
            lda: "pz",
            gga: "pbe",
            hybrid: "b3lyp",
        };
        let functional: string | undefined;
        if (!functionalStringOrObject) {
            functional = defaultFunctionals[subtype as string];
        } else {
            functional = safelyGetSlug(functionalStringOrObject as SlugifiedEntryOrSlug);
        }
        const path = `/pb/qm/dft/ksdft/${subtype}?functional=${functional}`;
        return allModels.find((categorized) => categorized.path === path);
    }

    static convertMlToCategorized(simpleModel: ModelConfig): SimplifiedCategorizedModel {
        const subtype = safelyGetSlug(simpleModel.subtype as SlugifiedEntryOrSlug);
        return {
            name: "Regression",
            path: "/st/det/ml/re/none",
            categories: {
                tier1: "st",
                tier2: "det",
                tier3: "ml",
                type: subtype,
            },
            parameters: {},
        };
    }
}
