import { BaseMethod } from "@mat3ra/esse/dist/js/types";

import { Method } from "../method";
import { PseudopotentialMethod } from "./pseudopotential";

export class MethodFactory {
    static Method = Method;

    static PseudopotentialMethod = PseudopotentialMethod;

    static create(config: BaseMethod): Method {
        switch (config.type) {
            case "pseudopotential":
                return new this.PseudopotentialMethod(config);
            default:
                return new this.Method(config);
        }
    }
}
