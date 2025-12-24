/* ANSI-C code produced by gperf version 3.1 */
/* Command-line: /usr/bin/gperf /home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf  */
/* Computed positions: -k'1-2' */

#if !((' ' == 32) && ('!' == 33) && ('"' == 34) && ('#' == 35) \
      && ('%' == 37) && ('&' == 38) && ('\'' == 39) && ('(' == 40) \
      && (')' == 41) && ('*' == 42) && ('+' == 43) && (',' == 44) \
      && ('-' == 45) && ('.' == 46) && ('/' == 47) && ('0' == 48) \
      && ('1' == 49) && ('2' == 50) && ('3' == 51) && ('4' == 52) \
      && ('5' == 53) && ('6' == 54) && ('7' == 55) && ('8' == 56) \
      && ('9' == 57) && (':' == 58) && (';' == 59) && ('<' == 60) \
      && ('=' == 61) && ('>' == 62) && ('?' == 63) && ('A' == 65) \
      && ('B' == 66) && ('C' == 67) && ('D' == 68) && ('E' == 69) \
      && ('F' == 70) && ('G' == 71) && ('H' == 72) && ('I' == 73) \
      && ('J' == 74) && ('K' == 75) && ('L' == 76) && ('M' == 77) \
      && ('N' == 78) && ('O' == 79) && ('P' == 80) && ('Q' == 81) \
      && ('R' == 82) && ('S' == 83) && ('T' == 84) && ('U' == 85) \
      && ('V' == 86) && ('W' == 87) && ('X' == 88) && ('Y' == 89) \
      && ('Z' == 90) && ('[' == 91) && ('\\' == 92) && (']' == 93) \
      && ('^' == 94) && ('_' == 95) && ('a' == 97) && ('b' == 98) \
      && ('c' == 99) && ('d' == 100) && ('e' == 101) && ('f' == 102) \
      && ('g' == 103) && ('h' == 104) && ('i' == 105) && ('j' == 106) \
      && ('k' == 107) && ('l' == 108) && ('m' == 109) && ('n' == 110) \
      && ('o' == 111) && ('p' == 112) && ('q' == 113) && ('r' == 114) \
      && ('s' == 115) && ('t' == 116) && ('u' == 117) && ('v' == 118) \
      && ('w' == 119) && ('x' == 120) && ('y' == 121) && ('z' == 122) \
      && ('{' == 123) && ('|' == 124) && ('}' == 125) && ('~' == 126))
/* The character set is not based on ISO-646.  */
#error "gperf generated tables don't work with this execution character set. Please report a bug to <bug-gperf@gnu.org>."
#endif

#line 5 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"

#include "../lookup.h"
#line 8 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
struct _LOOKUP;

#define IONTOTAL_KEYWORDS 28
#define IONMIN_WORD_LENGTH 1
#define IONMAX_WORD_LENGTH 2
#define IONMIN_HASH_VALUE 1
#define IONMAX_HASH_VALUE 47
/* maximum key range = 47, duplicates = 0 */

#ifdef __GNUC__
__inline
#else
#ifdef __cplusplus
inline
#endif
#endif
static unsigned int
_hash_ion (register const char *str, register size_t len)
{
  static unsigned char asso_values[] =
    {
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48,  1,  0, 15,  5, 23,
      48, 15, 48, 25, 20, 48,  0, 20, 10,  8,
      48, 18,  6,  3,  5, 30, 48, 48,  5, 48,
      48, 16, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
      48, 48, 48, 48, 48, 48, 48
    };
  register unsigned int hval = len;

  switch (hval)
    {
      default:
        hval += asso_values[(unsigned char)str[1]];
      /*FALLTHROUGH*/
      case 1:
        hval += asso_values[(unsigned char)str[0]+1];
        break;
    }
  return hval;
}

struct _LOOKUP *
_lookup_ion (register const char *str, register size_t len)
{
  static struct _LOOKUP wordlist[] =
    {
      {""},
#line 25 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"K", 9},
#line 11 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"AL", 9},
      {""}, {""},
#line 33 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"RB", 9},
#line 36 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"W", 9},
#line 17 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"CL", 9},
#line 15 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"CA", 9},
      {""},
#line 19 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"CS", 9},
#line 29 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"NA", 9},
#line 16 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"CD", 9},
#line 35 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"SR", 9},
      {""},
#line 18 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"CO", 9},
#line 21 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"F", 9},
#line 10 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"AG", 9},
#line 13 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"BA", 9},
      {""},
#line 31 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"PB", 9},
#line 24 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"I", 9},
#line 28 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"MN", 9},
#line 14 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"BR", 9},
      {""},
#line 32 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"PT", 9},
      {""},
#line 27 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"MG", 9},
#line 37 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"ZN", 9},
      {""},
#line 34 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"SE", 9},
      {""},
#line 12 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"AU", 9},
      {""}, {""},
#line 30 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"NI", 9},
      {""},
#line 20 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"CU", 9},
      {""}, {""},
#line 22 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"FE", 9},
      {""},
#line 23 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"HG", 9},
      {""}, {""}, {""}, {""},
#line 26 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/ion.gperf"
      {"LI", 9}
    };

  if (len <= IONMAX_WORD_LENGTH && len >= IONMIN_WORD_LENGTH)
    {
      register unsigned int key = _hash_ion (str, len);

      if (key <= IONMAX_HASH_VALUE)
        {
          register const char *s = wordlist[key].name;

          if (*str == *s && !strcmp (str + 1, s + 1))
            return &wordlist[key];
        }
    }
  return 0;
}
