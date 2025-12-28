import { ModelMethodFilter } from "@mat3ra/standata";
import { expect } from "chai";

describe("model-method filter", () => {
    const methodConfigs = [
        {
            name: "mock method A",
            units: [
                { path: "/qm/wf/none/smearing/gaussian" },
                { path: "/opt/diff/ordern/cg/none" },
                { path: "/qm/wf/none/psp/us" },
                { path: "/qm/wf/none/pw/none" },
            ],
        },
        {
            name: "mock method B",
            units: [
                { path: "/linalg/diag/none/davidson/none" },
                { path: "/qm/wf/none/psp/paw" },
                { path: "/qm/wf/none/pw/none" },
            ],
        },
        {
            name: "mock method C",
            units: [{ path: "/some/unsupported/method/path" }, { path: "/qm/wf/none/pw/none" }],
        },
    ];

    it("can filter a list of method by model parameters", () => {
        const modelConfig = {
            categories: { tier1: "pb", tier2: "qm", tier3: "dft", type: "ksdft", subtype: "lda" },
        };
        const modelMethodFilter = new ModelMethodFilter();
        const filteredConfigs = modelMethodFilter.getCompatibleMethods(modelConfig, methodConfigs);
        expect(filteredConfigs).to.have.length(2);
        expect(filteredConfigs.map((c) => c.name)).not.to.include("mock method C");
    });

    it("should return empty array if no filter assets are available", () => {
        const fakeModel = {
            categories: { tier1: "a", tier2: "b", tier3: "c", type: "d", subtype: "e" },
        };
        const modelMethodFilter = new ModelMethodFilter();
        const filteredConfigs = modelMethodFilter.getCompatibleMethods(fakeModel, methodConfigs);
        expect(filteredConfigs).to.have.length(0);
    });
});
