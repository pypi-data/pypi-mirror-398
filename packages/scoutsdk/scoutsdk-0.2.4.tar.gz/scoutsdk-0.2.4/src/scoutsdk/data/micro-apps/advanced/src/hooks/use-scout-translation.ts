import { useScoutAppContext } from '@mirego/scout-chat';
import { useCallback, useMemo } from 'react';
import strings from '../locales/strings.json';

export type ScoutTranslationFunction = (string: string) => string;

export interface ScoutTranslation {
  t: ScoutTranslationFunction;
}

const useScoutTranslation = () => {
  const { language } = useScoutAppContext();

  const t: ScoutTranslationFunction = useCallback(
    (string: string): string => {
      const languageKey =
        (Object.keys(strings).find(
          key => language.includes(key) || key.includes(language)
        ) as keyof typeof strings) || 'en';
      const languageStrings = strings[languageKey];
      if (string in languageStrings) {
        return languageStrings[string as keyof typeof languageStrings];
      }
      return string;
    },
    [language]
  );

  const returnValue: ScoutTranslation = useMemo(() => {
    return { t };
  }, [t]);

  return returnValue;
};

export default useScoutTranslation;
