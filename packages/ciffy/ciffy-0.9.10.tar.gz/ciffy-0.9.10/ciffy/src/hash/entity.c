/* ANSI-C code produced by gperf version 3.1 */
/* Command-line: /usr/bin/gperf /home/runner/work/ciffy/ciffy/ciffy/src/hash/entity.gperf  */
/* Computed positions: -k'' */

#line 5 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/entity.gperf"

#include "../lookup.h"
#line 8 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/entity.gperf"
struct _LOOKUP;

#define ENTITYTOTAL_KEYWORDS 5
#define ENTITYMIN_WORD_LENGTH 5
#define ENTITYMAX_WORD_LENGTH 11
#define ENTITYMIN_HASH_VALUE 5
#define ENTITYMAX_HASH_VALUE 11
/* maximum key range = 7, duplicates = 0 */

#ifdef __GNUC__
__inline
#else
#ifdef __cplusplus
inline
#endif
#endif
/*ARGSUSED*/
static unsigned int
_hash_entity (register const char *str, register size_t len)
{
  return len;
}

struct _LOOKUP *
_lookup_entity (register const char *str, register size_t len)
{
  static struct _LOOKUP wordlist[] =
    {
      {""}, {""}, {""}, {""}, {""},
#line 12 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/entity.gperf"
      {"water", 10},
      {""},
#line 10 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/entity.gperf"
      {"polymer", 12},
#line 13 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/entity.gperf"
      {"branched", 5},
#line 14 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/entity.gperf"
      {"macrolide", 8},
      {""},
#line 11 "/home/runner/work/ciffy/ciffy/ciffy/src/hash/entity.gperf"
      {"non-polymer", 8}
    };

  if (len <= ENTITYMAX_WORD_LENGTH && len >= ENTITYMIN_WORD_LENGTH)
    {
      register unsigned int key = _hash_entity (str, len);

      if (key <= ENTITYMAX_HASH_VALUE)
        {
          register const char *s = wordlist[key].name;

          if (*str == *s && !strcmp (str + 1, s + 1))
            return &wordlist[key];
        }
    }
  return 0;
}
