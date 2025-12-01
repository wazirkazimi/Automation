from vi import stack_videos

try:
    print('Calling stack_videos directly...')
    stack_videos('test_meme.mp4','test_gameplay.mp4','out_test.mp4', progress_callback=lambda p,m: print('PROGRESS',p,m))
    print('Done')
except Exception as e:
    import traceback
    traceback.print_exc()
    print('EXCEPTION STR:', e)
