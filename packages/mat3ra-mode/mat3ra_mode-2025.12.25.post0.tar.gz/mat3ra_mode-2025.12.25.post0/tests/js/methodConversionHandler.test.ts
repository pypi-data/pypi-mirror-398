import { MethodStandata } from "@mat3ra/standata";
import { expect } from "chai";

import { MethodConversionHandler } from "../../src/js";

const allMethods = new MethodStandata().getAll();

const CATEGORIZED_METHOD = {
    PSEUDOPOTENTIAL: allMethods.find((method) => {
        const pspUnits = method.units?.filter((unit) => unit.categories?.type === "psp") || [];
        return pspUnits.length === 1 && pspUnits[0].categories?.subtype === "nc";
    })!,
};

const SIMPLE_METHOD = {
    LOCAL_ORBITAL: {
        type: "localorbital",
        subtype: "pople",
    },
};

describe("MethodConversionHandler", () => {
    describe("convertToSimple", () => {
        it("converts categorized pseudopotential method to simple", () => {
            const simple = MethodConversionHandler.convertToSimple(
                CATEGORIZED_METHOD.PSEUDOPOTENTIAL,
            );

            expect(simple.type).to.equal("pseudopotential");
            expect(simple.subtype).to.equal("nc");
        });
    });

    describe("convertToCategorized", () => {
        it("converts simple local orbital method to categorized", () => {
            const categorized = MethodConversionHandler.convertToCategorized(
                SIMPLE_METHOD.LOCAL_ORBITAL,
                allMethods,
            );

            expect(categorized).to.exist;
            expect(categorized.path).to.equal("/qm/wf/none/ao/pople?basisSlug=6-31G");
            expect(categorized.units).to.be.an("array");
            expect(categorized.units[0].categories.subtype).to.equal("pople");
        });
    });
});
