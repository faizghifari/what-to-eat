# Profile Service

This service manages user profiles. Due to personal experience and preference, this service is written in Rust. Due to this, it has no runtime dependencies. To build, it requires only Cargo and the Rust toolchain (nightly) (see: [https://www.rust-lang.org/tools/install](https://www.rust-lang.org/tools/install)) and an internet connection.

### Request Information

Other services should communicate with the Profile service through TCP at port 5004. This section will present the desired structure of received messages.

In its most basic form, each request should be structured as followed:

1. Request code (3 digits). Example: `200`
2. User ID, delimited by `#id#` on either side. Example: `#id#7356#id#`
2. *(Optional)* Message

Therefore, the following request: <br>
`400#id#17926#id#` <br>
Would translate to a request for the dietary restrictions of the user with ID 17926.

There are no security checks in the Profile service, and it is assumed that the requesting service has already verified that such a request is appropriate. Speaking of security, this service assumes the presence of a file with the Supabase information on the backend in the `services` folder, named: `sb.uk` and containing the URL on the first line and API key on the second.


#### Request codes

The request codes currently supported are:

| Request | Code |
|---------|------|
|`GetProfile`|`100`|
|`EditProfile`|`200`|
|`GetPreferences`|`300`|
|`GetRestrictions`|`400`|
|`GetTools`|`500`|
|`GetIngredients`|`600`|
|`GetLocation`|`700`|

#### EditProfile

Only the `EditProfile` request requires an additional message. This message should be in JSON format and include the following information:

- Dietary Preferences: `list[String]`
- Dietary Restrictions: `list[String]`
- Available Tools: `list[String]`
- Available Ingredients: `list[String]`

For example:
```
{
  "preferences": ["eggs", "chicken", "jjigae"],
  "restrictions": ["fish", "pork"],
  "tools": ["microwave"],
  "ingredients": ["rice", "kimchi"]
}
```
or, in a request:
```
200#id#17876#id#{"preferences":["eggs","chicken","jjigae"],"restrictions":["fish","pork"],"tools":["microwave"],"ingredients":["rice","kimchi"]}

```
#### Data-only

If data size becomes a concern, there are many alternatives which can be dealt with later. A preliminary example would be encoding the request code in a single byte, the userID in the next 4 bytes (u32, approximately 1 billion possibilities), and representing the message in CBOR format. This implements the data transfer as pure bytes and not as a string to be deserialised and then parsed upon arrival.

For example:

| Request | Code (u8) |
|---------|------|
|`GetProfile`|`1`|
|`EditProfile`|`2`|
|`GetPreferences`|`3`|
|`GetRestrictions`|`4`|
|`GetTools`|`5`|
|`GetIngredients`|`6`|
|`GetLocation`|`7`|

Then, the following initial request becomes (Hex byte notation):
```
02 000045D4 A465746F6F6C7381696D6963726F776176656B696E6772656469656E7473826472696365666B696D6368696B707265666572656E63657383646567677367636869636B656E666A6A696761656C7265737472696374696F6E7382646669736864706F726B
```
For comparison, the original message would be transferred as:
```
323030 236964233137383736236964230a 7b22707265666572656e636573223a5b2265676773222c22636869636b656e222c226a6a69676165225d2c227265737472696374696f6e73223a5b2266697368222c22706f726b225d2c22746f6f6c73223a5b226d6963726f77617665225d2c22696e6772656469656e7473223a5b2272696365222c226b696d636869225d7d0a
```
