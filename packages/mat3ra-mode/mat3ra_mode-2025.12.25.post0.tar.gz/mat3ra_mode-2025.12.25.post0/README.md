[![npm version](https://badge.fury.io/js/%40mat3ra%2Fmode.svg)](https://badge.fury.io/js/%40mat3ra%2Fmode)
[![License: Apache](https://img.shields.io/badge/License-Apache-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

# mode

MOdel DEfinitions in JS/TS/Py - houses entity definitions for:

- `Method` - See [Method Overview](https://docs.mat3ra.com/methods/overview/)
- `Model` - See [Model Overview](https://docs.mat3ra.com/models/overview/)


### Installation

For usage within a JavaScript project:

```bash
npm install @mat3ra/mode
```

For development:

```bash
git clone https://github.com/Exabyte-io/mode.git
```


### Contribution

This repository is an [open-source](LICENSE.md) work-in-progress and we welcome contributions.

We regularly deploy the latest code containing all accepted contributions online as part of the
[Mat3ra.com](https://mat3ra.com) platform, so contributors will see their code in action there.

See [ESSE](https://github.com/Exabyte-io/esse) for additional context regarding the data schemas used here.

Useful commands for development:

```bash
# run linter without persistence
npm run lint

# run linter and save edits
npm run lint:fix

# compile the library
npm run transpile

# run tests
npm run test
```

#### How to Add New Models and Methods

!NOTE: this section is moved to [@mat3ra/standata](github.com/Exabyte-io/standata).

The list of model and method entities is compiled from Yaml assets located in the `./assets` directory
using the `build_entities.js` script. The assets processed by this script usually involve custom Yaml
types such as `!combine` to generate several entity configurations at once.

A new model or method may be added either by extending parameters of an existing entity or by adding
a new asset file such as the following:

```yaml
!combine
name:
  template: 'Model{{ "-" + parameters.example }}' # set the model name using a template

# Loop over parameters to create combinations
forEach:
  - !parameter
    key: parameters.example # path of where to set the property
    values: ["A", "B", "C"] # values to iterate over
    isOptional: true

# static configuration (same for all created entities
config:
  tags:
    - example_model
    - tutorial
  schema: !esse 'schema-id-placeholder' # add a schema using the !esse type to validate each configuration 
```

The above asset file will create four model configurations, "Model-A", "Model-B", "Model-C",
and "Model". The latter entity is created due to the `isOptional` flag of the example parameter.
There are a few more options available to customize the entity asset, for instance, the `!combine` type
has an `exclusions` property where conflicting pairs of entity properties can be defined, so that
combinations of those will be avoided.

For more examples, please see the asset files in `./assets` or [code.js](https://github.com/Exabyte-io/code.js)
for the definition of Yaml types such as `!combine` or `!parameter`.
