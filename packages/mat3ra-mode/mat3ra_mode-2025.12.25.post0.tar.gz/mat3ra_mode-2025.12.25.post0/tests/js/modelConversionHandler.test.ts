import { ModelStandata } from "@mat3ra/standata";
import { expect } from "chai";

import { ModelConversionHandler } from "../../src/js";

const allModels = new ModelStandata().getAll();

const CATEGORIZED_MODEL = {
    DFT: allModels.find(
        (model) =>
            model.categories?.tier3 === "dft" &&
            model.categories?.subtype === "lda" &&
            model.parameters?.functional === "pz",
    )!,
};

const EXPECTED_MODEL = {
    DFT: {
        SIMPLE: {
            type: "dft",
            subtype: "lda",
            functional: { slug: "pz", name: "pz" },
        },
        CATEGORIZED: {
            PATH: "/pb/qm/dft/ksdft/lda?functional=pz",
            FUNCTIONAL: "pz",
            SUBTYPE: "lda",
        },
    },
};

describe("ModelConversionHandler", () => {
    describe("convertToSimple", () => {
        it("converts categorized DFT model to simple", () => {
            const simple = ModelConversionHandler.convertToSimple(CATEGORIZED_MODEL.DFT);

            expect(simple).to.deep.equal(EXPECTED_MODEL.DFT.SIMPLE);
        });
    });

    describe("convertToCategorized", () => {
        it("converts simple DFT model to categorized", () => {
            const simple = ModelConversionHandler.convertToSimple(CATEGORIZED_MODEL.DFT);
            const categorized = ModelConversionHandler.convertToCategorized(simple, allModels);

            expect(categorized).to.exist;
            expect(categorized.path).to.equal(EXPECTED_MODEL.DFT.CATEGORIZED.PATH);
            expect(categorized.parameters.functional).to.equal(
                EXPECTED_MODEL.DFT.CATEGORIZED.FUNCTIONAL,
            );
            expect(categorized.categories.subtype).to.equal(EXPECTED_MODEL.DFT.CATEGORIZED.SUBTYPE);
        });
    });
});
