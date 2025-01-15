from locust import HttpUser, task, between
import os

video_name = "720x480_1mb.mp4"

class VideoProcessingUser(HttpUser):
    wait_time = between(1, 3)  # Temps d'attente entre les actions

    def on_start(self):
        self.video_id = None  # Initialise le video_id pour stocker l'identifiant soumis

    @task
    def complete_workflow(self):
        self.submit_video()
        if self.video_id:
            self.check_status_and_download()

    def submit_video(self):

        with open(video_name, "rb") as video_file:
            response = self.client.post(
                "/submit",
                files={"file": (video_name, video_file, "video/mp4")},
                data={"format": "mp4"}
            )
        
        if response.status_code == 200:
            self.video_id = response.json().get("video_id")
            print(f"Submitted video successfully, video_id: {self.video_id}")
        else:
            print(f"Failed to submit video. Status code: {response.status_code}")

    def check_status_and_download(self):
        for _ in range(10):  # Essaye plusieurs fois pour voir si le statut change
            response = self.client.get(f"/status/{self.video_id}")
            if response.status_code == 200:
                status = response.json().get("status", "processing")
                print(f"Video {self.video_id} status: {status}")
                if status == "completed":
                    self.download_video()
                    return
            self.wait_time()

    import os

    def download_video(self):
        response = self.client.get(f"/download/{self.video_id}")
        if response.status_code == 200:
            local_file_path = f"downloaded_{self.video_id}"
            with open(local_file_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded video {self.video_id} successfully.")

            # Suppression du fichier après téléchargement réussi
            try:
                os.remove(local_file_path)
                print(f"Deleted local file: {local_file_path}")
            except Exception as e:
                print(f"Failed to delete local file {local_file_path}: {e}")
        else:
            print(f"Failed to download video {self.video_id}. Status code: {response.status_code}")

