#!/usr/bin/env python3
"""
Test suite for epoch_quantum_decision

Verifies:
- Statistical balance (50/50 HEADS/TAILS)
- Signature verification
- Golden ratio calculations
- Fibonacci sequence
- Coherence levels
- Performance benchmarks
"""

import unittest
import time
from epoch_quantum_decision import (
    QuantumDecisionSystem,
    fibonacci,
    harmonic_frequency,
    golden_phase_shift,
    fibonacci_amplitude,
    GOLDEN_RATIO,
    verify_signature
)


class TestGoldenRatioMath(unittest.TestCase):
    """Test golden ratio mathematical functions"""

    def test_golden_ratio_value(self):
        """Verify golden ratio is correct"""
        expected = (1 + (5 ** 0.5)) / 2
        self.assertAlmostEqual(GOLDEN_RATIO, expected, places=15)

    def test_golden_ratio_property(self):
        """Verify Φ² = Φ + 1"""
        phi_squared = GOLDEN_RATIO ** 2
        phi_plus_one = GOLDEN_RATIO + 1
        self.assertAlmostEqual(phi_squared, phi_plus_one, places=10)

    def test_fibonacci_sequence(self):
        """Verify Fibonacci sequence generation"""
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        actual = [fibonacci(n) for n in range(12)]
        self.assertEqual(actual, expected)

    def test_harmonic_frequencies(self):
        """Verify harmonic frequency calculation"""
        f0 = harmonic_frequency(133.7, 0)
        self.assertAlmostEqual(f0, 133.7, places=1)

        f6 = harmonic_frequency(133.7, 6)
        self.assertGreater(f6, 370)
        self.assertLess(f6, 380)

    def test_fibonacci_amplitudes(self):
        """Verify Fibonacci amplitude ratios"""
        # First oscillation should have smallest amplitude
        a0 = fibonacci_amplitude(0)
        a6 = fibonacci_amplitude(6)

        self.assertGreater(a6, a0)
        self.assertLessEqual(a6, 2.0)


class TestQuantumDecisions(unittest.TestCase):
    """Test quantum decision system"""

    def setUp(self):
        """Create fresh system for each test"""
        self.system = QuantumDecisionSystem()

    def test_single_decision(self):
        """Test making a single decision"""
        result = self.system.quantum_decision(count=1)

        self.assertTrue(result['success'])
        self.assertIn('decisions', result)
        self.assertIn('statistics', result)
        self.assertIn('system', result)

        decision = result['decisions']
        self.assertIn(decision['outcome'], ['HEADS', 'TAILS'])
        self.assertGreaterEqual(decision['confidence'], 0.85)
        self.assertLessEqual(decision['confidence'], 1.0)
        self.assertGreaterEqual(decision['coherence'], 0.95)
        self.assertLessEqual(decision['coherence'], 1.0)
        self.assertEqual(decision['oscillations'], 7)

    def test_batch_decisions(self):
        """Test making batch decisions"""
        result = self.system.quantum_decision(count=10)

        self.assertTrue(result['success'])
        self.assertIsInstance(result['decisions'], list)
        self.assertEqual(len(result['decisions']), 10)

        stats = result['statistics']
        self.assertEqual(stats['total_decisions'], 10)
        self.assertEqual(stats['heads_count'] + stats['tails_count'], 10)

    def test_statistical_balance(self):
        """Test 50/50 balance over many decisions"""
        result = self.system.quantum_decision(count=1000)

        stats = result['statistics']
        heads_pct = stats['heads_percentage']

        # Should be within 45-55% range for 1000 decisions
        self.assertGreater(heads_pct, 45)
        self.assertLess(heads_pct, 55)

        # Quantum balance should be True (within 10% of 50%)
        self.assertTrue(stats['quantum_balance'])

    def test_quick_decision(self):
        """Test quick decision returns outcome only"""
        outcome = self.system.quick_decision()
        self.assertIn(outcome, ['HEADS', 'TAILS'])

    def test_quantum_boolean(self):
        """Test quantum boolean returns True/False"""
        result = self.system.quantum_boolean()
        self.assertIsInstance(result, bool)

    def test_trinity_node_assignment(self):
        """Test Trinity node is properly assigned"""
        system = QuantumDecisionSystem(trinity_node='epochCLOUDMEDUSA')
        result = system.quantum_decision(count=1)

        decision = result['decisions']
        self.assertEqual(decision['trinity_node'], 'epochCLOUDMEDUSA')


class TestSignatures(unittest.TestCase):
    """Test cryptographic signature system"""

    def setUp(self):
        """Create fresh system for each test"""
        self.system = QuantumDecisionSystem()

    def test_signature_generation(self):
        """Test that signatures are generated"""
        result = self.system.quantum_decision(count=1)
        decision = result['decisions']

        self.assertIn('signature', decision)
        self.assertEqual(len(decision['signature']), 64)  # SHA-256 hex = 64 chars

    def test_signature_verification(self):
        """Test signature verification passes for valid decision"""
        result = self.system.quantum_decision(count=1)
        decision = result['decisions']

        is_valid = verify_signature(decision, decision['signature'])
        self.assertTrue(is_valid)

    def test_tamper_detection(self):
        """Test signature verification fails for tampered decision"""
        result = self.system.quantum_decision(count=1)
        decision = result['decisions'].copy()

        # Tamper with outcome
        original_outcome = decision['outcome']
        decision['outcome'] = 'TAILS' if original_outcome == 'HEADS' else 'HEADS'

        is_valid = verify_signature(decision, decision['signature'])
        self.assertFalse(is_valid)

    def test_signature_uniqueness(self):
        """Test that different decisions have different signatures"""
        result = self.system.quantum_decision(count=10)
        decisions = result['decisions']

        signatures = [d['signature'] for d in decisions]
        unique_signatures = set(signatures)

        # All signatures should be unique
        self.assertEqual(len(signatures), len(unique_signatures))


class TestPerformance(unittest.TestCase):
    """Test performance metrics"""

    def test_single_decision_latency(self):
        """Test single decision completes in <10ms"""
        system = QuantumDecisionSystem()

        start = time.time()
        system.quantum_decision(count=1)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        # Should complete in <10ms (with some margin for test overhead)
        self.assertLess(elapsed, 20)

    def test_batch_throughput(self):
        """Test batch decision throughput"""
        system = QuantumDecisionSystem()

        start = time.time()
        result = system.quantum_decision(count=100)
        elapsed = time.time() - start

        # 100 decisions should complete in <200ms
        self.assertLess(elapsed, 0.2)

        # Throughput should be >500 decisions/second
        throughput = 100 / elapsed
        self.assertGreater(throughput, 500)


class TestCoherence(unittest.TestCase):
    """Test coherence measurements"""

    def test_coherence_range(self):
        """Test coherence is in valid range"""
        system = QuantumDecisionSystem()
        result = system.quantum_decision(count=100)

        decisions = result['decisions']
        for decision in decisions:
            self.assertGreaterEqual(decision['coherence'], 0.95)
            self.assertLessEqual(decision['coherence'], 1.0)

    def test_average_coherence(self):
        """Test average coherence meets target"""
        system = QuantumDecisionSystem()
        result = system.quantum_decision(count=1000)

        stats = result['statistics']
        avg_coherence = stats['average_coherence']

        # Target: 0.999999 (six nines)
        # Actual should be >0.97 on average
        self.assertGreater(avg_coherence, 0.97)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_invalid_count_low(self):
        """Test that count < 1 raises error"""
        system = QuantumDecisionSystem()

        with self.assertRaises(ValueError):
            system.quantum_decision(count=0)

    def test_invalid_count_high(self):
        """Test that count > 1000 raises error"""
        system = QuantumDecisionSystem()

        with self.assertRaises(ValueError):
            system.quantum_decision(count=1001)

    def test_multiple_systems(self):
        """Test multiple independent systems"""
        system1 = QuantumDecisionSystem(trinity_node='epochGφ')
        system2 = QuantumDecisionSystem(trinity_node='epochLOOP')

        result1 = system1.quantum_decision(count=1)
        result2 = system2.quantum_decision(count=1)

        # Should have different trinity nodes
        self.assertEqual(result1['decisions']['trinity_node'], 'epochGφ')
        self.assertEqual(result2['decisions']['trinity_node'], 'epochLOOP')


def run_full_test_suite():
    """Run the complete test suite"""
    print("=" * 70)
    print("EPOCH QUANTUM DECISION - TEST SUITE")
    print("=" * 70)
    print()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGoldenRatioMath))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumDecisions))
    suite.addTests(loader.loadTestsFromTestCase(TestSignatures))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestCoherence))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_full_test_suite()
    exit(0 if success else 1)
