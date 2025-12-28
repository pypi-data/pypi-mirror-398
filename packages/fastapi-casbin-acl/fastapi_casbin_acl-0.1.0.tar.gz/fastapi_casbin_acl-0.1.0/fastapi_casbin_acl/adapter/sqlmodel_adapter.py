"""
Async SQLModel Adapter for Casbin policy storage.
"""
from typing import Callable, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from casbin.persist.adapters.asyncio.adapter import AsyncAdapter
from casbin.persist.adapter import load_policy_line

from .orm import CasbinRule


class SQLModelAdapter(AsyncAdapter):
    """
    Async SQLModel adapter for Casbin.
    
    This adapter stores Casbin policies in a database using SQLModel/SQLAlchemy.
    It requires an async session factory function that returns an AsyncSession.
    
    Example:
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        
        engine = create_async_engine("mysql+aiomysql://user:pass@localhost/db")
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        adapter = SQLModelAdapter(async_session)
    """
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        """
        Initialize the adapter with an async session factory.
        
        :param session_factory: A callable that returns an AsyncSession instance.
                               Typically an async_sessionmaker instance.
        """
        self._session_factory = session_factory
    
    async def load_policy(self, model):
        """
        Load all policy rules from the database.
        
        :param model: The Casbin model to load policies into.
        """
        async with self._session_factory() as session:
            result = await session.execute(select(CasbinRule))
            rules = result.scalars().all()
            
            for rule in rules:
                # Build policy line: "ptype, v0, v1, v2, ..."
                values = [rule.v0, rule.v1, rule.v2, rule.v3, rule.v4, rule.v5]
                # Filter out None values
                values = [v for v in values if v is not None]
                policy_line = f"{rule.ptype}, {', '.join(values)}"
                
                load_policy_line(policy_line, model)
    
    async def save_policy(self, model):
        """
        Save all policy rules to the database.
        
        This method clears existing policies and saves all policies from the model.
        
        :param model: The Casbin model containing policies to save.
        """
        async with self._session_factory() as session:
            # Clear existing policies
            await session.execute(delete(CasbinRule))
            await session.commit()
            
            # Save policies
            policies_to_save = []
            
            # Process policy rules (p)
            if "p" in model.model.keys():
                for key, ast in model.model["p"].items():
                    for pvals in ast.policy:
                        rule = self._create_rule("p", pvals)
                        policies_to_save.append(rule)
            
            # Process role definitions (g)
            if "g" in model.model.keys():
                for key, ast in model.model["g"].items():
                    for pvals in ast.policy:
                        rule = self._create_rule("g", pvals)
                        policies_to_save.append(rule)
            
            # Bulk insert
            if policies_to_save:
                session.add_all(policies_to_save)
                await session.commit()
    
    def _create_rule(self, ptype: str, values: List[str]) -> CasbinRule:
        """
        Create a CasbinRule from policy values.
        
        :param ptype: Policy type ("p" or "g")
        :param values: List of policy values
        :return: CasbinRule instance
        """
        # Pad values to 6 fields (v0-v5)
        padded_values = (values + [None] * 6)[:6]
        
        return CasbinRule(
            ptype=ptype,
            v0=padded_values[0],
            v1=padded_values[1],
            v2=padded_values[2],
            v3=padded_values[3],
            v4=padded_values[4],
            v5=padded_values[5],
        )
    
    async def add_policy(self, sec: str, ptype: str, rule: List[str]) -> bool:
        """
        Add a single policy rule to the database.
        
        :param sec: Section name (usually "p" or "g")
        :param ptype: Policy type
        :param rule: List of policy values
        :return: True if the policy was added successfully
        """
        async with self._session_factory() as session:
            casbin_rule = self._create_rule(ptype, rule)
            session.add(casbin_rule)
            await session.commit()
            return True
    
    async def remove_policy(self, sec: str, ptype: str, rule: List[str]) -> bool:
        """
        Remove a single policy rule from the database.
        
        :param sec: Section name (usually "p" or "g")
        :param ptype: Policy type
        :param rule: List of policy values to match
        :return: True if the policy was removed successfully
        """
        async with self._session_factory() as session:
            # Build query to match the rule
            query = select(CasbinRule).where(CasbinRule.ptype == ptype)
            
            # Match each field
            if len(rule) > 0:
                query = query.where(CasbinRule.v0 == rule[0])
            if len(rule) > 1:
                query = query.where(CasbinRule.v1 == rule[1])
            if len(rule) > 2:
                query = query.where(CasbinRule.v2 == rule[2])
            if len(rule) > 3:
                query = query.where(CasbinRule.v3 == rule[3])
            if len(rule) > 4:
                query = query.where(CasbinRule.v4 == rule[4])
            if len(rule) > 5:
                query = query.where(CasbinRule.v5 == rule[5])
            
            result = await session.execute(query)
            rules_to_delete = result.scalars().all()
            
            if rules_to_delete:
                for rule in rules_to_delete:
                    await session.delete(rule)
                await session.commit()
                return True
            
            return False
    
    async def remove_filtered_policy(
        self, sec: str, ptype: str, field_index: int, *field_values: str
    ) -> bool:
        """
        Remove policy rules that match the filter from the database.
        
        :param sec: Section name (usually "p" or "g")
        :param ptype: Policy type
        :param field_index: Starting index of the field to filter on
        :param field_values: Values to match for fields starting at field_index
        :return: True if any policies were removed
        """
        async with self._session_factory() as session:
            query = select(CasbinRule).where(CasbinRule.ptype == ptype)
            
            # Apply filters based on field_index
            field_mapping = {
                0: CasbinRule.v0,
                1: CasbinRule.v1,
                2: CasbinRule.v2,
                3: CasbinRule.v3,
                4: CasbinRule.v4,
                5: CasbinRule.v5,
            }
            
            for i, value in enumerate(field_values):
                field_idx = field_index + i
                if field_idx < 6:
                    query = query.where(field_mapping[field_idx] == value)
            
            result = await session.execute(query)
            rules_to_delete = result.scalars().all()
            
            if rules_to_delete:
                for rule in rules_to_delete:
                    await session.delete(rule)
                await session.commit()
                return True
            
            return False

