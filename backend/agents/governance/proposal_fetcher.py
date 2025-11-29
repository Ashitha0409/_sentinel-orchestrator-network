"""
ProposalFetcher Agent
====================
Fetches governance proposal metadata from IPFS and Blockfrost.
"""

import httpx
import json
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class ProposalMetadata:
    """Structured proposal metadata"""
    title: str
    abstract: str
    motivation: str
    rationale: str
    amount: int  # In lovelace
    ipfs_hash: str
    references: List[str]
    error: Optional[str] = None

class ProposalFetcher:
    """
    Agent responsible for fetching proposal metadata from IPFS.
    Supports CIP-100/108 format.
    """
    
    # Multiple IPFS gateways for redundancy
    IPFS_GATEWAYS = [
        "https://ipfs.io/ipfs/",
        "https://cloudflare-ipfs.com/ipfs/",
        "https://gateway.pinata.cloud/ipfs/",
        "https://dweb.link/ipfs/"
    ]
    
    def __init__(self):
        self.logger = logging.getLogger("SON.ProposalFetcher")
        self.logger.info("ProposalFetcher initialized")
    
    async def fetch_metadata(
        self,
        ipfs_hash: str,
        timeout: int = 15
    ) -> ProposalMetadata:
        """
        Fetch CIP-100/108 metadata from IPFS with fallback gateways.
        
        Args:
            ipfs_hash: IPFS content hash (e.g., "QmXyz...")
            timeout: Request timeout in seconds
            
        Returns:
            ProposalMetadata object with parsed data
        """
        for gateway in self.IPFS_GATEWAYS:
            url = f"{gateway}{ipfs_hash}"
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        metadata = response.json()
                        
                        # Validate CIP-100 structure
                        if "body" in metadata:
                            body = metadata['body']
                            return ProposalMetadata(
                                title=body.get('title', 'Untitled Proposal'),
                                abstract=body.get('abstract', '')[:500],
                                motivation=body.get('motivation', '')[:2000],
                                rationale=body.get('rationale', '')[:2000],
                                amount=body.get('amount', 0),
                                references=body.get('references', [])[:5],
                                ipfs_hash=ipfs_hash
                            )
                        
            except Exception as e:
                self.logger.debug(f"Gateway {gateway} failed: {e}")
                continue
        
        # All gateways failed
        return ProposalMetadata(
            title="Metadata Unavailable",
            abstract="[IPFS retrieval failed]",
            motivation="",
            rationale="",
            amount=0,
            references=[],
            ipfs_hash=ipfs_hash,
            error="All IPFS gateways unreachable"
        )
    
    def generate_log(self, metadata: ProposalMetadata) -> str:
        """Generate Matrix-style terminal log output"""
        return f"""
[PROPOSAL FETCHER] Metadata Retrieved
├─ Title: {metadata.title[:50]}
├─ Amount: {metadata.amount / 1_000_000:,.0f} ADA
├─ IPFS Hash: {metadata.ipfs_hash[:16]}...
└─ Status: {'✓ Success' if not metadata.error else '✗ ' + metadata.error}
        """
