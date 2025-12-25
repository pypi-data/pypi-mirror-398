"""
Modality Commands - ModalitySwitcher routing (EXPERIMENTAL)

Handles LLM adapter routing based on epistemic state.
This is experimental functionality not required for core Empirica operation.
"""

import json
import logging
from ..cli_utils import handle_cli_error, parse_json_safely

logger = logging.getLogger(__name__)


def handle_modality_route_command(args):
    """Handle modality routing command - routes to optimal LLM adapter (EXPERIMENTAL)"""
    try:
        from empirica.plugins.modality_switcher.modality_switcher import ModalitySwitcher, RoutingPreferences, RoutingStrategy
        
        logger.info(f"🔄 Running epistemic adaptive routing: {args.question}")
        logger.warning("⚠️  EXPERIMENTAL: ModalitySwitcher is experimental and not required for core Empirica")
        
        # Parse context and epistemic vectors from CLI args
        context = parse_json_safely(getattr(args, 'context', None)) or {}
        
        # Parse individual epistemic vectors if provided as CLI args
        epistemic_state = {}
        if hasattr(args, 'epistemic_state') and args.epistemic_state:
            epistemic_json = parse_json_safely(args.epistemic_state)
            if epistemic_json:
                epistemic_state.update(epistemic_json)
        else:
            # Check for individual vector args
            vector_attrs = {
                'know': getattr(args, 'know', None),
                'do': getattr(args, 'do', None),
                'context': getattr(args, 'context_vec', None),
                'uncertainty': getattr(args, 'uncertainty', None),
                'clarity': getattr(args, 'clarity', None),
                'coherence': getattr(args, 'coherence', None),
                'signal': getattr(args, 'signal', None),
                'density': getattr(args, 'density', None),
                'state': getattr(args, 'state', None),
                'change': getattr(args, 'change', None),
                'completion': getattr(args, 'completion', None),
                'impact': getattr(args, 'impact', None),
                'engagement': getattr(args, 'engagement', None)
            }
            
            for vector, value in vector_attrs.items():
                if value is not None:
                    try:
                        epistemic_state[vector] = float(value)
                    except (ValueError, TypeError):
                        pass
        
        # Determine routing strategy
        strategy = getattr(args, 'strategy', 'epistemic')
        force_adapter = getattr(args, 'adapter', None)
        max_cost = getattr(args, 'max_cost', 1.0)
        max_latency = getattr(args, 'max_latency', 30.0)
        min_quality = getattr(args, 'min_quality', 0.7)
        allow_fallback = not getattr(args, 'no_fallback', False)
        
        # Create routing preferences
        if force_adapter:
            routing_preferences = RoutingPreferences(
                force_adapter=force_adapter,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        elif strategy == 'cost':
            routing_preferences = RoutingPreferences(
                strategy=RoutingStrategy.COST,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        elif strategy == 'latency':
            routing_preferences = RoutingPreferences(
                strategy=RoutingStrategy.LATENCY,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        elif strategy == 'quality':
            routing_preferences = RoutingPreferences(
                strategy=RoutingStrategy.QUALITY,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        elif strategy == 'balanced':
            routing_preferences = RoutingPreferences(
                strategy=RoutingStrategy.BALANCED,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        else:  # Default to epistemic
            routing_preferences = RoutingPreferences(
                strategy=RoutingStrategy.EPISTEMIC,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        
        # Create and use modality switcher
        logger.info("🎯 Determining optimal adapter...")
        switcher = ModalitySwitcher()
        decision = switcher.route_request(
            query=args.question,
            epistemic_state=epistemic_state,
            preferences=routing_preferences,
            context=context
        )
        
        logger.info(f"   Selected: {decision.selected_adapter}")
        logger.info(f"   Rationale: {decision.rationale}")
        logger.info(f"   Estimated: ${decision.estimated_cost:.4f}, {decision.estimated_latency:.1f}s")
        
        if getattr(args, 'verbose', False):
            logger.info(f"   Fallbacks: {decision.fallback_adapters}")
            if not getattr(args, 'yes', False):
                try:
                    response = input("   Proceed? [Y/n] ").lower()
                    if response and response not in ['y', 'yes']:
                        logger.info("   ❌ Cancelled by user")
                        return
                except (EOFError, KeyboardInterrupt):
                    logger.info("   ⏩ Proceeding (non-interactive mode)")
        
        # Execute the request
        result = switcher.execute_with_routing(
            query=args.question,
            epistemic_state=epistemic_state,
            preferences=routing_preferences,
            context=context,
            system="You are a helpful assistant with metacognitive awareness.",
            temperature=0.7,
            max_tokens=1000
        )
        
        if hasattr(result, 'decision'):
            logger.info(f"✅ Execution complete")
            logger.info(f"   🎯 Decision: {result.decision}")
            logger.info(f"   📊 Confidence: {result.confidence:.2f}")
            logger.info(f"   💭 Rationale: {result.rationale[:100]}{'...' if len(result.rationale) > 100 else ''}")
            
            if getattr(args, 'verbose', False):
                logger.info("   🧠 Vector References:")
                for vector, value in result.vector_references.items():
                    logger.info(f"      📊 {vector}: {value:.2f}")
                
                logger.info("   🚀 Suggested Actions:")
                for action in result.suggested_actions:
                    logger.info(f"      • {action}")
        else:
            logger.error(f"❌ Execution failed: {result.message if hasattr(result, 'message') else result}")
        
        # Show usage statistics
        if getattr(args, 'verbose', False):
            stats = switcher.get_usage_stats()
            logger.info(f"📈 Usage Stats: {stats}")
        
    except Exception as e:
        handle_cli_error(e, "Modality routing", getattr(args, 'verbose', False))


def handle_decision_command(args):
    """Handle decision-making command with uncertainty assessment (EXPERIMENTAL)"""
    try:
        from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

        print(f"⚖️ Analyzing decision: {args.decision}")
        logger.warning("⚠️  EXPERIMENTAL: This is experimental functionality")
        
        context = parse_json_safely(getattr(args, 'context', None))
        confidence_threshold = getattr(args, 'confidence_threshold', 0.7)
        
        # Run epistemic cascade for decision-making
        cascade_result = run_epistemic_cascade(
            task=f"Should I proceed with: {args.decision}",
            context=context or {},
            confidence_threshold=confidence_threshold
        )
        
        logger.info(f"✅ Decision analysis complete")
        logger.info(f"   🎯 Decision: {cascade_result.get('final_decision', 'INVESTIGATE')}")
        logger.info(f"   📊 Confidence: {cascade_result.get('confidence', 0.0):.2f}")
        logger.info(f"   ⚖️ Threshold: {confidence_threshold}")
        
        # Recommendation
        meets_threshold = cascade_result.get('confidence', 0.0) >= confidence_threshold
        recommendation = "PROCEED" if meets_threshold else "INVESTIGATE FURTHER"
        emoji = "✅" if meets_threshold else "⚠️"
        
        logger.info(f"   {emoji} Recommendation: {recommendation}")
        logger.info(f"   💭 Reasoning: {cascade_result.get('reasoning', 'N/A')}")
        
        # Show epistemic state
        epistemic_state = cascade_result.get('epistemic_state', {})
        if epistemic_state and getattr(args, 'verbose', False):
            logger.info("🧠 Epistemic State:")
            if 'know' in epistemic_state:
                logger.info(f"   📚 KNOW: {epistemic_state['know']:.2f}")
            if 'do' in epistemic_state:
                logger.info(f"   ⚡ DO: {epistemic_state['do']:.2f}")
            if 'context' in epistemic_state:
                logger.info(f"   🌐 CONTEXT: {epistemic_state['context']:.2f}")
        
        # Show next steps
        if cascade_result.get('required_actions'):
            logger.info("⚡ Next steps:")
            for action in cascade_result['required_actions']:
                logger.info(f"   • {action}")
        
        # Show investigation history
        if getattr(args, 'verbose', False) and cascade_result.get('investigation_history'):
            logger.info("🔍 Investigation history:")
            for i, investigation in enumerate(cascade_result['investigation_history'], 1):
                logger.info(f"   {i}. {investigation.get('action', 'Unknown')}")
        
    except Exception as e:
        handle_cli_error(e, "Decision analysis", getattr(args, 'verbose', False))
