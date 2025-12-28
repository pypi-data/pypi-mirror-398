import { expect } from "chai";

import {
    getDefaultModelSubtypeForApplicationAndType,
    getDefaultModelTypeForApplication,
    getTreeByApplicationNameAndVersion,
} from "../../src/js/tree";

const testCasesAppNameAndVersion = [
    {
        app: { name: "espresso", version: "6.3" },
        expectedKeys: ["dft"],
        expectedSubkeys: ["gga", "lda", "hybrid"],
    },
    {
        app: { name: "vasp", version: "5.4.4" },
        expectedKeys: ["dft"],
    },
    {
        app: { name: "python", version: "3.8.6" },
        expectedKeys: ["unknown"],
        expectedSubkeys: ["unknown"],
    },
    {
        app: { name: "non-existent-app", version: "1.0.0" },
        expectedKeys: [],
    },
];

const testCasesDefaultType = [
    { app: { name: "espresso", version: "6.3" }, expected: "dft" },
    { app: { name: "vasp", version: "5.4.4" }, expected: "dft" },
    { app: { name: "python", version: "3.8.6" }, expected: "unknown" },
    { app: { name: "non-existent-app", version: "1.0.0" }, expected: undefined },
];

const testCasesDefaultSubtype = [
    { app: { name: "espresso", version: "6.3" }, type: "dft", expected: "gga" },
    { app: { name: "vasp", version: "5.4.4" }, type: "dft", expected: "gga" },
    { app: { name: "nwchem", version: "7.0.2" }, type: "dft", expected: "gga" },
    { app: { name: "python", version: "3.8.6" }, type: "unknown", expected: "unknown" },
    { app: { name: "shell", version: "0.0.1" }, type: "unknown", expected: "unknown" },
    {
        app: { name: "non-existent-app", version: "1.0.0" },
        type: "dft",
        expected: undefined,
    },
    {
        app: { name: "espresso", version: "6.3" },
        type: "non-existent-type",
        expected: undefined,
    },
];

const testCasesModelConfig = [
    {
        app: { name: "espresso", version: "6.3" },
        expectedType: "dft",
        expectedSubtype: "gga",
    },
    {
        app: { name: "vasp", version: "5.4.4" },
        expectedType: "dft",
        expectedSubtype: "gga",
    },
    {
        app: { name: "python", version: "3.8.6" },
        expectedType: "unknown",
        expectedSubtype: "unknown",
    },
    {
        app: { name: "non-existent-app", version: "1.0.0" },
        expectedType: undefined,
        expectedSubtype: undefined,
    },
];

describe("tree", () => {
    it("can getTreeByApplicationNameAndVersion", () => {
        testCasesAppNameAndVersion.forEach(({ app, expectedKeys, expectedSubkeys }) => {
            const tree = getTreeByApplicationNameAndVersion(app);
            expect(tree).to.be.an("object");
            expect(Object.keys(tree)).to.have.length(expectedKeys.length);

            expectedKeys.forEach((key) => {
                expect(tree).to.have.property(key);
            });

            if (expectedSubkeys && expectedKeys[0]) {
                expectedSubkeys.forEach((subkey) => {
                    expect(tree[expectedKeys[0]]).to.have.property(subkey);
                });
            }
        });
    });

    it("can getDefaultModelTypeForApplication", () => {
        testCasesDefaultType.forEach(({ app, expected }) => {
            const type = getDefaultModelTypeForApplication(app);
            expect(type).to.equal(expected);
        });
    });

    it("can getDefaultModelSubtypeForApplicationAndType", () => {
        testCasesDefaultSubtype.forEach(({ app, type, expected }) => {
            const subtype = getDefaultModelSubtypeForApplicationAndType(app, type);
            expect(subtype).to.equal(expected);
        });
    });

    it("can get complete model config", () => {
        testCasesModelConfig.forEach(({ app, expectedType, expectedSubtype }) => {
            const type = getDefaultModelTypeForApplication(app);
            const subtype = type
                ? getDefaultModelSubtypeForApplicationAndType(app, type)
                : undefined;

            expect(type).to.equal(expectedType);
            expect(subtype).to.equal(expectedSubtype);
        });
    });
});
