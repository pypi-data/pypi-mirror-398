/* ANSI-C code produced by gperf version 3.1 */
/* Command-line: /usr/bin/gperf /home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf  */
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

#line 5 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"

#include "../lookup.h"
#line 8 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
struct _LOOKUP;

#define ELEMENTTOTAL_KEYWORDS 35
#define ELEMENTMIN_WORD_LENGTH 1
#define ELEMENTMAX_WORD_LENGTH 2
#define ELEMENTMIN_HASH_VALUE 1
#define ELEMENTMAX_HASH_VALUE 92
/* maximum key range = 92, duplicates = 0 */

#ifdef __GNUC__
__inline
#else
#ifdef __cplusplus
inline
#endif
#endif
static unsigned int
_hash_element (register const char *str, register size_t len)
{
  static unsigned char asso_values[] =
    {
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93,  6, 30, 55,  0, 50,
      93, 25, 93, 20, 45, 93, 10,  1, 10,  5,
      40, 30, 35,  1, 35, 50, 93, 93, 15, 93,
      93, 20, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93, 93, 93, 93,
      93, 93, 93, 93, 93, 93, 93
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
_lookup_element (register const char *str, register size_t len)
{
  static struct _LOOKUP wordlist[] =
    {
      {""},
#line 12 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"C", 6},
#line 36 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"CD", 48},
#line 38 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"CS", 55},
      {""}, {""},
#line 13 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"N", 7},
#line 26 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"CO", 27},
#line 23 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"CA", 20},
      {""}, {""},
#line 22 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"K", 19},
#line 21 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"CL", 17},
#line 16 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"NA", 11},
      {""}, {""},
#line 40 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"W", 74},
#line 34 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"MO", 42},
      {""}, {""}, {""},
#line 10 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"H", 1},
#line 24 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"MN", 25},
#line 11 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"LI", 3},
      {""}, {""},
#line 15 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"F", 9},
#line 27 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"NI", 28},
      {""}, {""}, {""},
#line 19 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"P", 15},
#line 29 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"ZN", 30},
#line 32 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"RB", 37},
      {""}, {""},
#line 20 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"S", 16},
#line 17 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"MG", 12},
      {""}, {""}, {""},
#line 14 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"O", 8},
#line 18 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"AL", 13},
      {""}, {""}, {""},
#line 37 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"I", 53},
#line 43 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"HG", 80},
      {""}, {""}, {""}, {""},
#line 28 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"CU", 29},
      {""}, {""}, {""}, {""},
#line 35 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"AG", 47},
      {""}, {""}, {""}, {""},
#line 44 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"PB", 82},
#line 39 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"BA", 56},
      {""}, {""}, {""},
#line 41 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"PT", 78},
      {""}, {""}, {""}, {""},
#line 33 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"SR", 38},
      {""}, {""}, {""}, {""},
#line 25 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"FE", 26},
      {""}, {""}, {""}, {""},
#line 42 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"AU", 79},
      {""}, {""}, {""}, {""},
#line 30 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"SE", 34},
      {""}, {""}, {""}, {""},
#line 31 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/element.gperf"
      {"BR", 35}
    };

  if (len <= ELEMENTMAX_WORD_LENGTH && len >= ELEMENTMIN_WORD_LENGTH)
    {
      register unsigned int key = _hash_element (str, len);

      if (key <= ELEMENTMAX_HASH_VALUE)
        {
          register const char *s = wordlist[key].name;

          if (*str == *s && !strcmp (str + 1, s + 1))
            return &wordlist[key];
        }
    }
  return 0;
}
