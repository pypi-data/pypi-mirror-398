import { Model } from "../model";
import {
    getDefaultModelSubtypeForApplicationAndType,
    getDefaultModelTypeForApplication,
    getTreeByApplicationNameAndVersion,
} from "../tree";
import type { ModelConfig } from "../types";
import { DFTModel } from "./dft";

export class ModelFactory {
    static DFTModel = DFTModel;

    static Model = Model;

    static create(config: ModelConfig): Model {
        switch (config.type) {
            case "dft":
                return new this.DFTModel(config);
            default:
                return new this.Model(config);
        }
    }

    static createFromApplication(config: ModelConfig): Model {
        const { application } = config;
        if (!application) {
            throw new Error("ModelFactory.createFromApplication: application is required");
        }

        const tree = getTreeByApplicationNameAndVersion(application);
        if (Object.keys(tree).length === 0) {
            return this.create({ ...config, type: "unknown", subtype: "unknown" });
        }

        const type = getDefaultModelTypeForApplication(application);
        const subtype = getDefaultModelSubtypeForApplicationAndType(application, type) || "unknown";

        return this.create({ ...config, type, subtype });
    }
}
