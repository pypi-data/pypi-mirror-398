import retextSpell from "retext-spell";
import memoize from "memoizee";

async function loadDictionary(locale) {
  const baseUrl = new URL(`https://unpkg.com/dictionary-${locale}@latest/`);

  const [aff, dic] = await Promise.all([
    fetch(new URL("index.aff", baseUrl)),
    fetch(new URL("index.dic", baseUrl)),
  ]);

  if (!(aff.ok && dic.ok)) {
    throw new Error(`Couldn't load dictionary files from ${baseUrl}`);
  }
  return {
    aff: Buffer.from(await aff.arrayBuffer()),
    dic: Buffer.from(await dic.arrayBuffer()),
  };
}

async function _createSpellPluginForLocale(locale, personalDictionary) {
  const dictionary = await loadDictionary(locale);
  return retextSpell({ dictionary, personal: personalDictionary.join("\n") });
}
const createSpellPluginForLocale = memoize(_createSpellPluginForLocale, {
  promise: true,
});
// Pre-load the EN dictionary
createSpellPluginForLocale("en");

export const name = "retext-spell";
export async function plugin(spellConfig) {
  const { dictionary: locale, "personal-dictionary": personalDictionary } =
    spellConfig;
  return await createSpellPluginForLocale(locale, personalDictionary);
}
