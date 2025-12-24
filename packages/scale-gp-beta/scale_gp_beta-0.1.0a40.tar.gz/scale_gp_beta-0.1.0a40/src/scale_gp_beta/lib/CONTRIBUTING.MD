# Custom Code Patch
You can in theory add custom code patches to anywhere in the repo but at the risk of encountering many merge conflicts with Stainless into the future.
Stainless will never use the `/lib` and `/examples` directories. When possible try to only modify these directories.
If you have to add custom code elsewhere, please keep the footprint small and create a library for most of the logic.


For information on custom code patching with Stainless see [here](https://www.stainless.com/docs/guides/add-custom-code).

# Process for Adding Features
Checkout the `next` branch and pull, then create a branch from `next`.

> **_NOTE:_** Stainless uses next to "queue up" updates to the SDK.
> 
> Stainless will update next with their own logic updates to the SDK along with any changes in the OpenAPI spec and changes to the Stainless
config on their SaaS platform.

Make any code changes you need. Ensuring all the tests for the library are passing.

There is strict linting in this repo. Use the following commands in order.

```bash
rye lint --fix
```

```bash
rye run lint | grep /specific_file.py
```

`rye run lint` will not work if there are errors with `rye lint --fix`.
I am unsure why but I get many errors which are ignorable in the rest of the repo when running `rye run lint` so I usually use it
with grep to target the file I am developing.

> **_NOTE:_** The strict linting requires all types to be strictly typed. This can be a pain but is worth considering before developing any new solution.
> Try and avoid using ignore commands when possible, but sometimes it is unavoidable (see OpenAI tracing Plugin).

When commiting, use the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) spec. Usually this is something like:

```bash
git commit -m "feat: Added OpenAI tracing processor"
```
This allow Stainless to update the release doc with more useful info.

**When creating a PR, you must manually change the destination from `main` to `next`.**

Once merged, Stainless should pick up the changes and update or create a new PR for `main`.
You will need to accept changes on this PR, Stainless should then auto merge. Note on occasion I have had to manually merge.
There was no consequence to this.

These PRs Stainless makes have 4 types of changes, all are merged to main via these automatic PR requests:
1. Custom Code Changes
2. Stainless SDK logic changes
3. Changes to the Stainless Config in the SaaS platform
4. Changes to the OpenAPI schema