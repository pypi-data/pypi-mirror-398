import { expect } from "chai";

import { ModelFactory } from "../../src/js/models/factory";

const testCasesConfigs = [
    {
        config: { type: "dft", subtype: "gga" },
        expectedClass: "DFTModel",
        expectedType: "dft",
        expectedSubtype: "gga",
    },
    {
        config: { type: "unknown", subtype: "unknown" },
        expectedClass: "Model",
        expectedType: "unknown",
        expectedSubtype: "unknown",
    },
];

const testCasesFromApplication = [
    {
        app: { name: "espresso", version: "6.3" },
        expectedClass: "DFTModel",
        expectedType: "dft",
        expectedSubtype: "gga",
    },
    {
        app: { name: "vasp", version: "5.4.4" },
        expectedClass: "DFTModel",
        expectedType: "dft",
        expectedSubtype: "gga",
    },
    {
        app: { name: "nwchem", version: "7.0.2" },
        expectedClass: "DFTModel",
        expectedType: "dft",
        expectedSubtype: "gga",
    },
    {
        app: { name: "python", version: "3.8.6" },
        expectedClass: "Model",
        expectedType: "unknown",
        expectedSubtype: "unknown",
    },
    {
        app: { name: "non-existent-app", version: "1.0.0" },
        expectedClass: "Model",
        expectedType: "unknown",
        expectedSubtype: "unknown",
    },
];
describe("ModelFactory", () => {
    it("can create", () => {
        testCasesConfigs.forEach(({ config, expectedClass, expectedType, expectedSubtype }) => {
            const model = ModelFactory.create(config);

            expect(model).to.exist;
            expect(model.constructor.name).to.equal(expectedClass);
            expect(model.type).to.equal(expectedType);
            expect(model.subtype).to.equal(expectedSubtype);
        });
    });

    it("can createFromApplication", () => {
        testCasesFromApplication.forEach(
            ({ app, expectedClass, expectedType, expectedSubtype }) => {
                const model = ModelFactory.createFromApplication({ application: app });

                expect(model).to.exist;
                expect(model.constructor.name).to.equal(expectedClass);
                expect(model.type).to.equal(expectedType);
                expect(model.subtype).to.equal(expectedSubtype);
            },
        );
    });

    it("throws error if application is not provided", () => {
        expect(() => {
            ModelFactory.createFromApplication({} as any);
        }).to.throw("ModelFactory.createFromApplication: application is required");
    });

    it("can createFromApplication with method", () => {
        const model = ModelFactory.createFromApplication({
            application: { name: "espresso", version: "6.3" },
            method: { type: "pseudopotential", subtype: "us" },
        });

        expect(model).to.exist;
        expect(model.type).to.equal("dft");
        expect(model.subtype).to.equal("gga");
        expect(model.Method).to.exist;
        expect(model.Method.type).to.equal("pseudopotential");
        expect(model.Method.subtype).to.equal("us");
    });

    it("can createFromApplication with additional properties", () => {
        const model = ModelFactory.createFromApplication({
            application: { name: "espresso", version: "6.3" },
            functional: "pbe",
        });

        expect(model).to.exist;
        expect(model.type).to.equal("dft");
        expect(model.subtype).to.equal("gga");
        // @ts-ignore - accessing DFTModel specific property
        expect(model.functional).to.equal("pbe");
    });

    it("does not create incomplete models (regression test)", () => {
        // Original bug: models were created with only type, missing subtype
        const model = ModelFactory.createFromApplication({
            application: { name: "espresso", version: "6.3" },
        });

        expect(model.type).to.exist;
        expect(model.type).to.equal("dft");
        expect(model.subtype).to.exist;
        expect(model.subtype).to.equal("gga");

        // Verify no errors when accessing subtype (would throw if missing)
        expect(() => {
            const { subtype } = model;
            return subtype;
        }).to.not.throw();
    });
});
