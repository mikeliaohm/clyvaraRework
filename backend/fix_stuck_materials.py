#!/usr/bin/env python3
"""
Script to fix stuck materials in processing status.

This script will:
1. Identify materials stuck in "processing" status
2. Clean up old stuck materials (0% progress for >1 hour)
3. Optionally retry processing for stuck materials
"""

import sys
from datetime import datetime, timedelta
from database import get_db, Material
from models.rag import RagDocument
from sqlalchemy.orm import Session

def check_stuck_materials():
    """Check for materials stuck in processing status"""
    db = next(get_db())
    
    # Get all processing materials
    processing = db.query(Material).filter(
        Material.user_id == 'SYSTEM',
        Material.status == 'processing'
    ).all()
    
    if not processing:
        print("✅ No materials stuck in processing status!")
        return []
    
    print(f"⏳ Found {len(processing)} materials in processing status:\n")
    
    stuck_materials = []
    active_materials = []
    
    for m in processing:
        # Check how long it's been processing
        time_diff = datetime.now() - m.uploaded_at
        hours = time_diff.total_seconds() / 3600
        
        # Check if there are any vector entries (means processing started)
        vector_count = db.query(RagDocument).filter(
            RagDocument.material_id == m.id,

        ).count()
        
        print(f"📄 {m.title}")
        print(f"   ID: {m.id}")
        print(f"   Progress: {m.processing_progress}%")
        print(f"   Processing Time: {hours:.2f} hours")
        print(f"   Vector Entries: {vector_count}")
        
        # Consider stuck if:
        # 1. 0% progress for >1 hour, OR
        # 2. No progress for >24 hours
        if m.processing_progress == 0 and hours > 1:
            print(f"   ⚠️  STUCK: 0% progress for {hours:.2f} hours")
            stuck_materials.append(m)
        elif hours > 24:
            print(f"   ⚠️  STUCK: Processing for {hours:.2f} hours")
            stuck_materials.append(m)
        elif m.processing_progress > 0:
            print(f"   ✓ Active: {m.processing_progress}% complete")
            active_materials.append(m)
        
        print()
    
    return stuck_materials, active_materials

def clean_stuck_materials(stuck_materials, action='mark_failed'):
    """Clean up stuck materials"""
    db = next(get_db())
    
    if not stuck_materials:
        print("✅ No stuck materials to clean up!")
        return
    
    print(f"🧹 Cleaning up {len(stuck_materials)} stuck materials...\n")
    
    for m in stuck_materials:
        print(f"📄 {m.title} (ID: {m.id})")
        
        if action == 'delete':
            # Delete vector entries first
            vectors = db.query(RagDocument).filter(
                RagDocument.material_id == m.id,
    
            ).all()
            
            for v in vectors:
                db.delete(v)
            
            # Delete material
            db.delete(m)
            print(f"   ✓ Deleted material and {len(vectors)} vector entries")
        
        elif action == 'mark_failed':
            # Mark as failed
            m.status = 'failed'
            m.processing_error = 'Processing timeout - stuck in processing status'
            db.commit()
            print(f"   ✓ Marked as failed")
        
        print()
    
    db.commit()
    print(f"✅ Cleaned up {len(stuck_materials)} stuck materials!")

def remove_duplicates():
    """Remove duplicate materials (keep the one with highest progress)"""
    db = next(get_db())
    
    # Get all system materials
    all_materials = db.query(Material).filter(Material.user_id == 'SYSTEM').all()
    
    # Group by title
    titles = {}
    for m in all_materials:
        if m.title in titles:
            titles[m.title].append(m)
        else:
            titles[m.title] = [m]
    
    # Find duplicates
    duplicates = {title: mats for title, mats in titles.items() if len(mats) > 1}
    
    if not duplicates:
        print("✅ No duplicate materials found!")
        return
    
    print(f"🧹 Found {len(duplicates)} duplicate materials:\n")
    
    to_delete = []
    
    for title, mats in duplicates.items():
        print(f"📄 {title}: {len(mats)} entries")
        
        # Sort by: processed > processing (by progress) > failed
        def sort_key(m):
            if m.status == 'processed':
                return (0, m.chunk_count, m.id)
            elif m.status == 'processing':
                return (1, m.processing_progress, m.id)
            else:
                return (2, 0, m.id)
        
        mats_sorted = sorted(mats, key=sort_key)
        keep = mats_sorted[0]
        delete = mats_sorted[1:]
        
        print(f"   ✓ Keeping: ID {keep.id} (Status: {keep.status}, Progress: {keep.processing_progress}%)")
        
        for m in delete:
            print(f"   ✗ Deleting: ID {m.id} (Status: {m.status}, Progress: {m.processing_progress}%)")
            to_delete.append(m)
        print()
    
    # Delete duplicates
    for m in to_delete:
        # Delete vector entries first
        vectors = db.query(RagDocument).filter(
            RagDocument.material_id == m.id,

        ).all()
        
        for v in vectors:
            db.delete(v)
        
        # Delete material
        db.delete(m)
        print(f"✓ Deleted material ID {m.id} and {len(vectors)} vector entries")
    
    db.commit()
    print(f"\n✅ Removed {len(to_delete)} duplicate materials!")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix stuck materials in processing status")
    parser.add_argument('--check', action='store_true', help='Check for stuck materials')
    parser.add_argument('--clean', action='store_true', help='Clean up stuck materials')
    parser.add_argument('--action', choices=['delete', 'mark_failed'], default='mark_failed',
                        help='Action to take on stuck materials (default: mark_failed)')
    parser.add_argument('--remove-duplicates', action='store_true', help='Remove duplicate materials')
    parser.add_argument('--all', action='store_true', help='Run all cleanup tasks')
    
    args = parser.parse_args()
    
    if args.all:
        args.check = True
        args.clean = True
        args.remove_duplicates = True
    
    if not any([args.check, args.clean, args.remove_duplicates]):
        args.check = True
    
    if args.check:
        stuck, active = check_stuck_materials()
        
        if active:
            print(f"\n✓ {len(active)} materials are still actively processing")
            print("   These should complete automatically - no action needed")
        
        if stuck:
            print(f"\n⚠️  {len(stuck)} materials are stuck and need cleanup")
            print(f"   Run with --clean to fix them")
    
    if args.clean:
        stuck, _ = check_stuck_materials()
        if stuck:
            confirm = input(f"\n⚠️  This will {args.action} {len(stuck)} stuck materials. Continue? (y/n): ")
            if confirm.lower() == 'y':
                clean_stuck_materials(stuck, action=args.action)
            else:
                print("Cancelled.")
        else:
            print("✅ No stuck materials to clean up!")
    
    if args.remove_duplicates:
        confirm = input(f"\n⚠️  This will remove duplicate materials. Continue? (y/n): ")
        if confirm.lower() == 'y':
            remove_duplicates()
        else:
            print("Cancelled.")

if __name__ == "__main__":
    main()







