
#ifndef _IN_CSP_AUTOGEN_CSP_IMPL_TYPES_AUTOGEN_TYPES
#define _IN_CSP_AUTOGEN_CSP_IMPL_TYPES_AUTOGEN_TYPES

#include <csp/core/Exception.h>
#include <csp/engine/Struct.h>
#include <cstddef>

namespace csp::autogen
{

class TimeIndexPolicy : public csp::CspEnum
{
public:
    // Raw value quick access
    enum class enum_
    {
        INCLUSIVE = 1,
        EXCLUSIVE = 2,
        EXTRAPOLATE = 3
    };

    // CspEnum types
    static TimeIndexPolicy INCLUSIVE;
    static TimeIndexPolicy EXCLUSIVE;
    static TimeIndexPolicy EXTRAPOLATE;

    const char * asCString() const                { return name().c_str(); }
    const std::string & asString() const          { return name(); }

    static TimeIndexPolicy create( enum_ v )          { return s_meta -> create( ( int64_t ) v ); }
    static TimeIndexPolicy create( const char * name) { return s_meta -> fromString( name ); }
    static TimeIndexPolicy create( const std::string & s ) { return create( s.c_str() ); }

    enum_ enum_value() const { return ( enum_ ) value(); }

    static constexpr uint32_t num_types() { return 3; }

    static bool static_init();

    TimeIndexPolicy( const csp::CspEnum & v ) : csp::CspEnum( v ) { CSP_TRUE_OR_THROW( v.meta() == s_meta.get(), AssertionError, "Mismatched enum meta" ); }

private:

    static std::shared_ptr<csp::CspEnumMeta> s_meta;
};

class DynamicBasketEvent : public csp::Struct
{
public:

    using Ptr = csp::TypedStructPtr<DynamicBasketEvent>;

    DynamicBasketEvent()  = delete;
    ~DynamicBasketEvent() = delete;
    DynamicBasketEvent( const DynamicBasketEvent & ) = delete;
    DynamicBasketEvent( DynamicBasketEvent && ) = delete;

    Ptr copy() const { return csp::structptr_cast<DynamicBasketEvent>( Struct::copy() ); }

    static DynamicBasketEvent::Ptr create()
    {
        return Ptr( static_cast<DynamicBasketEvent *>( s_meta -> createRaw() ) );
    }

    static const csp::StructMetaPtr & meta() { return s_meta; }


    const csp::DialectGenericType & key() const
    {
        static_assert( offsetof( DynamicBasketEvent,m_key ) == 0 );
        static_assert( alignof( csp::DialectGenericType ) == 8 );
        static_assert( sizeof( csp::DialectGenericType ) == 8 );

        if( !key_isSet() )
            CSP_THROW( csp::ValueError, "field key on struct DynamicBasketEvent is not set" );

        return m_key;
    }

    void set_key( const csp::DialectGenericType & value )
    {
        
        static_assert( offsetof( DynamicBasketEvent,m_key ) == 0 );
        static_assert( alignof( csp::DialectGenericType ) == 8 );
        static_assert( sizeof( csp::DialectGenericType ) == 8 );

        m_DynamicBasketEvent_mask[0] |= 1;


        //TODO employ move semantics where it makes sense
        m_key = value;
    }

    

    bool key_isSet() const
    {
        static_assert(( offsetof( DynamicBasketEvent,m_DynamicBasketEvent_mask) + 0 ) == 9 );
        return m_DynamicBasketEvent_mask[0] & 1;
    }

    void clear_key()
    {
        static_assert(( offsetof( DynamicBasketEvent,m_DynamicBasketEvent_mask) + 0 ) == 9 );
        m_DynamicBasketEvent_mask[0] &= ~1;
    }

    const bool & added() const
    {
        static_assert( offsetof( DynamicBasketEvent,m_added ) == 8 );
        static_assert( alignof( bool ) == 1 );
        static_assert( sizeof( bool ) == 1 );

        if( !added_isSet() )
            CSP_THROW( csp::ValueError, "field added on struct DynamicBasketEvent is not set" );

        return m_added;
    }

    void set_added( const bool & value )
    {
        
        static_assert( offsetof( DynamicBasketEvent,m_added ) == 8 );
        static_assert( alignof( bool ) == 1 );
        static_assert( sizeof( bool ) == 1 );

        m_DynamicBasketEvent_mask[0] |= 2;


        //TODO employ move semantics where it makes sense
        m_added = value;
    }

    

    bool added_isSet() const
    {
        static_assert(( offsetof( DynamicBasketEvent,m_DynamicBasketEvent_mask) + 0 ) == 9 );
        return m_DynamicBasketEvent_mask[0] & 2;
    }

    void clear_added()
    {
        static_assert(( offsetof( DynamicBasketEvent,m_DynamicBasketEvent_mask) + 0 ) == 9 );
        m_DynamicBasketEvent_mask[0] &= ~2;
    }


    static bool static_init();

private:

    csp::DialectGenericType m_key;
    bool m_added;
    char m_DynamicBasketEvent_mask[1];


    static csp::StructMetaPtr s_meta;

    static void assert_mask()
    {
        static_assert( offsetof( DynamicBasketEvent, m_DynamicBasketEvent_mask ) == 9 );
    }
};

class DynamicBasketEvents : public csp::Struct
{
public:

    using Ptr = csp::TypedStructPtr<DynamicBasketEvents>;

    DynamicBasketEvents()  = delete;
    ~DynamicBasketEvents() = delete;
    DynamicBasketEvents( const DynamicBasketEvents & ) = delete;
    DynamicBasketEvents( DynamicBasketEvents && ) = delete;

    Ptr copy() const { return csp::structptr_cast<DynamicBasketEvents>( Struct::copy() ); }

    static DynamicBasketEvents::Ptr create()
    {
        return Ptr( static_cast<DynamicBasketEvents *>( s_meta -> createRaw() ) );
    }

    static const csp::StructMetaPtr & meta() { return s_meta; }


    const std::vector<csp::autogen::DynamicBasketEvent::Ptr> & events() const
    {
        static_assert( offsetof( DynamicBasketEvents,m_events ) == 0 );
        static_assert( alignof( std::vector<csp::autogen::DynamicBasketEvent::Ptr> ) == 8 );
        static_assert( sizeof( std::vector<csp::autogen::DynamicBasketEvent::Ptr> ) == 24 );

        if( !events_isSet() )
            CSP_THROW( csp::ValueError, "field events on struct DynamicBasketEvents is not set" );

        return m_events;
    }

    void set_events( const std::vector<csp::autogen::DynamicBasketEvent::Ptr> & value )
    {
        
        static_assert( offsetof( DynamicBasketEvents,m_events ) == 0 );
        static_assert( alignof( std::vector<csp::autogen::DynamicBasketEvent::Ptr> ) == 8 );
        static_assert( sizeof( std::vector<csp::autogen::DynamicBasketEvent::Ptr> ) == 24 );

        m_DynamicBasketEvents_mask[0] |= 1;


        //TODO employ move semantics where it makes sense
        m_events = value;
    }

    

    bool events_isSet() const
    {
        static_assert(( offsetof( DynamicBasketEvents,m_DynamicBasketEvents_mask) + 0 ) == 24 );
        return m_DynamicBasketEvents_mask[0] & 1;
    }

    void clear_events()
    {
        static_assert(( offsetof( DynamicBasketEvents,m_DynamicBasketEvents_mask) + 0 ) == 24 );
        m_DynamicBasketEvents_mask[0] &= ~1;
    }


    static bool static_init();

private:

    std::vector<csp::autogen::DynamicBasketEvent::Ptr> m_events;
    char m_DynamicBasketEvents_mask[1];


    static csp::StructMetaPtr s_meta;

    static void assert_mask()
    {
        static_assert( offsetof( DynamicBasketEvents, m_DynamicBasketEvents_mask ) == 24 );
    }
};

}
#endif