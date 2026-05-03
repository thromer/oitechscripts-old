//! Make changes in https://github.com/olympiaindivisible/oitechscripts/src

class AppError extends Error {}

function doGet() {
  hardcodedExampleStartOwnershipTransfer();
}

function hardcodedExampleStartOwnershipTransfer() {
  // TODO: error handling, backoff, rate limiting, ...
  const EMAIL = "theromer9@gmail.com";
  const RECIPIENT = "tromer@gmail.com";
  const EXAMPLE_FILE_ID_2 = "1_OFmQLkxv1Msfos0Q8nI8dx9hu8R4YlZfC_NjU9_e1w"; // "departing user's file in subfolder"

  const fileId = EXAMPLE_FILE_ID_2;
  // const parentId = Drive.Files.get(fileId, {fields: "parents(id)"}).parents[0].id;
  // eslint -disable-next-line @typescript-eslint/no-non-null-assertion
  const parentId = Drive_v2?.Files.get(fileId, { fields: "parents(id)" })
    ?.parents?.[0]?.id;
  console.log("parentId", parentId);
  if (!parentId) {
    throw new AppError("Unable to find parent folder");
  }
  // TODO: memoize transferCandidates per folder
  const transferCandidates = Drive_v2?.Permissions.list(parentId, {
    fields: "items(emailAddress,type,role)",
  })
    .items?.filter(
      (p) =>
        (p.role === "writer" || p.role === "owner") &&
        p.type === "user" &&
        p.emailAddress !== EMAIL,
    )
    .map((p) => p.emailAddress); // we'll assume we've already filtered by owner === EMAIL
  console.log("transferCandidates", JSON.stringify(transferCandidates));
  if (!transferCandidates?.includes(RECIPIENT)) {
    throw new Error(`${RECIPIENT} has to be an editor or owner on the folder`);
  }
  console.log(
    "before",
    JSON.stringify(
      Drive_v2?.Permissions.list(fileId, {
        fields: "items(emailAddress,type,role,id,pendingOwner)",
      }).items?.filter((p) => p.emailAddress === RECIPIENT),
    ),
  );
  // TODO: tsc will complain about 'pendingOwner' until https://github.com/DefinitelyTyped/DefinitelyTyped/pull/74949 is released. Until then, monkey-patch it in.
  const response = Drive_v2?.Permissions.insert(
    { role: "writer", type: "user", value: RECIPIENT, pendingOwner: true },
    fileId,
    { fields: "emailAddress,type,role,id,pendingOwner" },
  );
  console.log("response", JSON.stringify(response));
  console.log(
    "after",
    JSON.stringify(
      Drive_v2?.Permissions.list(fileId, {
        fields: "items(emailAddress,type,role,id,pendingOwner)",
      }).items?.filter((p) => p.emailAddress === RECIPIENT),
    ),
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
(globalThis as any).doGet = doGet;
