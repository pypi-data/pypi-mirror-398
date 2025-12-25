#ifndef BITFSM_OPT_PACK_H_
#define BITFSM_OPT_PACK_H_

namespace bitfsm_opt {

// A compile-time container for a collection of type parameters.
//
// We use this instead of std::tuple to make it clear that this is a
// compile-time construct, rather than a runtime type.
template<typename... Types>
struct Pack {};

// PackElement<I, P>::type returns the I'th element of the pack P.
template<std::size_t, typename...>
struct PackElement {};

template<std::size_t kIndex, typename Head, typename... Tail>
requires (sizeof...(Tail) >= kIndex)
struct PackElement<kIndex, Pack<Head, Tail...>>
    : PackElement<kIndex - 1, Pack<Tail...>>
{};

template<typename Head, typename... Tail>
struct PackElement<0, Pack<Head, Tail...>> {
  using type = Head;
};

}

#endif // BITFSM_OPT_PACK_H_
