#pragma once
#include <cstddef>
#include <cstdint>

namespace ghidra {
class Architecture;
class AddrSpace;
class Action;
class Rule;
class PcodeOp;
class Funcdata;
} // namespace ghidra

namespace reoxide {

class ReOxideInterface;
class Plugin {
public:
    virtual ~Plugin() { }
};

struct Context {
    ghidra::Architecture* arch;
    ghidra::AddrSpace* stackspace;
    ReOxideInterface* reoxide;
};

struct InitArgs {
    const char* group_name;
    uint64_t extra_arg;
};

typedef ghidra::Action* ActionCnstr(const Context*, Plugin*, const InitArgs*);
typedef ghidra::Rule* RuleCnstr(const Context*, Plugin*, const InitArgs*);

struct ActionDefinition {
    const char* name;
    ActionCnstr* cnstr;
};

struct RuleDefinition {
    const char* name;
    RuleCnstr* cnstr;
};

// We use these definitions for plugins that are not using the C++ ABI,
// but plugins where everything is wrapped using a generated C ABI
extern "C" {
struct OpaqueAction;
struct OpaqueRule;
struct StdVectorOpCode;

typedef OpaqueAction* CActionCnstr(const Context*, Plugin*, const InitArgs*);
typedef void CActionDestroy(OpaqueAction*);
typedef int32_t CActionApply(OpaqueAction*, ghidra::Funcdata*);
typedef OpaqueRule* CRuleCnstr(const Context*, Plugin*, const InitArgs*);
typedef void CRuleOpList(const OpaqueRule*, StdVectorOpCode*);
typedef int32_t CRuleApplyOp(OpaqueRule*, ghidra::PcodeOp*, ghidra::Funcdata*);
typedef void CRuleDestroy(OpaqueRule*);

struct CActionDefinition {
    const char* name;
    CActionCnstr* cnstr;
    CActionDestroy* destroy;
    CActionApply* apply;
};

struct CRuleDefinition {
    const char* name;
    CRuleCnstr* cnstr;
    CRuleDestroy* destroy;
    CRuleOpList* oplist;
    CRuleApplyOp* apply;
};
}

#define REOXIDE_RULES(...)                                                          \
    extern "C" const reoxide::RuleDefinition reoxide_rule_defs[] = { __VA_ARGS__ }; \
    extern "C" const size_t reoxide_rule_count = sizeof(reoxide_rule_defs) / sizeof(reoxide::RuleDefinition);
#define REOXIDE_ACTIONS(...)                                                            \
    extern "C" const reoxide::ActionDefinition reoxide_action_defs[] = { __VA_ARGS__ }; \
    extern "C" const size_t reoxide_action_count = sizeof(reoxide_action_defs) / sizeof(reoxide::ActionDefinition);
#define REOXIDE_CONTEXT(x)                                         \
    extern "C" reoxide::Plugin* reoxide_plugin_new()               \
    {                                                              \
        return new x {};                                           \
    }                                                              \
    extern "C" void reoxide_plugin_delete(reoxide::Plugin* plugin) \
    {                                                              \
        delete plugin;                                             \
    }

} // namespace reoxide
