import { expect } from "chai";

import { Model } from "../../src/js/model";
import { DFTModel } from "../../src/js/models/dft";
import { ModelConfig } from "../../src/js/types";

describe("Model", () => {
    // @ts-ignore
    const obj: ModelConfig = { type: "dft" };

    it("can be created", () => {
        const app = new Model(obj);
        expect(app.type).to.equal("dft");
    });

    describe("modelSchemaMixin property access", () => {
        it("should return string for type property", () => {
            const model = new Model({ type: "dft", subtype: "gga" });
            const typeValue = model.type;

            expect(typeValue).to.be.a("string");
            expect(typeValue).to.equal("dft");
        });

        it("should return string or object for subtype property", () => {
            const model = new Model({ type: "dft", subtype: "gga" });
            const subtypeValue = model.subtype;

            expect(subtypeValue).to.exist;
            expect(subtypeValue).to.equal("gga");
        });

        it("should return Method instance for method property", () => {
            const model = new Model({
                type: "dft",
                subtype: "gga",
                method: { type: "pseudopotential", subtype: "nc" },
            });

            const methodValue = model.Method;

            // Check that method is an instance, not a plain object
            expect(methodValue).to.exist;
            expect(methodValue.constructor.name).to.not.equal("Object");

            // Check that it has Method class methods
            expect(methodValue).to.have.property("setSearchText");
            // @ts-ignore
            expect(methodValue).to.have.property("setData");
            expect(methodValue.setData).to.be.a("function");
        });
    });

    describe("DFTModel with method", () => {
        it("should return Method instance (not plain object) for method property", () => {
            const dftModel = new DFTModel({
                type: "dft",
                subtype: "gga",
                functional: "pbe",
                method: { type: "pseudopotential", subtype: "nc" },
            });

            const methodValue = dftModel.Method;

            // Check that method is an instance, not a plain object
            expect(methodValue).to.exist;
            expect(methodValue.constructor.name).to.not.equal("Object");

            // Check that it has Method class methods
            expect(methodValue).to.have.property("setSearchText");
            expect(methodValue.setSearchText).to.be.a("function");
        });
    });
});
